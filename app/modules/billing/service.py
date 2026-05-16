import stripe
from facturapi import Facturapi
from app.core.config import settings
from app.modules.organizations.repository import OrganizationRepository
from .repository import BillingRepository
import logging
from fastapi import HTTPException
from app.core.events import publish_event
from app.core.models import OutboxEvent
from sqlalchemy import text
from datetime import datetime, timezone

logger = logging.getLogger("modules.billing.service")

# Stripe & Facturapi Initialization
stripe.api_key = settings.get("STRIPE_SECRET_KEY")
facturapi = Facturapi(settings.get("FACTURAPI_KEY")) if settings.get("FACTURAPI_KEY") else None

PLAN_PRICE_MAPPING = {
    "plan_medico": settings.get("STRIPE_PRICE_MEDICO"),
    "plan_consultorio": settings.get("STRIPE_PRICE_CONSULTORIO"),
    "plan_clinica_premium": settings.get("STRIPE_PRICE_CLINICA"),
}

class BillingService:
    def __init__(self, repo: BillingRepository, org_repo: OrganizationRepository):
        self.repo = repo
        self.org_repo = org_repo

    async def create_checkout_session(self, org_id: str, plan_code: str, success_url: str, cancel_url: str):
        """
        Creates a Stripe Checkout Session for a subscription.
        """
        org = await self.org_repo.get(org_id)
        if not org:
            raise HTTPException(404, "Organization not found")

        price_id = PLAN_PRICE_MAPPING.get(plan_code)
        if not price_id:
            raise HTTPException(400, "Invalid plan code or price not configured")

        try:
            # Check if customer already exists
            customer_id = org.get("stripe_customer_id")
            
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                customer_email=None if customer_id else None, # Could use admin email
                payment_method_types=['card'],
                line_items=[{'price': price_id, 'quantity': 1}],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "org_id": org_id,
                    "plan_code": plan_code
                }
            )
            return checkout_session.url
        except Exception as e:
            logger.error(f"Stripe Checkout Error: {str(e)}")
            raise HTTPException(500, "Error creating payment session")

    async def create_portal_session(self, org_id: str, return_url: str):
        """
        Creates a Stripe Customer Portal session.
        """
        org = await self.org_repo.get(org_id)
        customer_id = org.get("stripe_customer_id")
        
        if not customer_id:
            raise HTTPException(400, "No active subscription found for this organization")

        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return session.url
        except Exception as e:
            logger.error(f"Stripe Portal Error: {str(e)}")
            raise HTTPException(500, "Error creating management portal")

    async def handle_webhook(self, payload: str, sig_header: str):
        """
        Orchestrates webhook processing.
        """
        webhook_secret = settings.get("STRIPE_WEBHOOK_SECRET")
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except Exception as e:
            logger.error(f"Webhook Signature Error: {str(e)}")
            raise ValueError("Invalid signature")

        await self.repo.log_webhook(event.type, event.to_dict())

        # Logic for specific events
        if event.type == "checkout.session.completed":
            await self._process_checkout_completed(event.data.object)
        elif event.type == "invoice.paid":
            await self._process_invoice_paid(event.data.object)
        elif event.type in ["customer.subscription.updated", "customer.subscription.deleted"]:
            await self._process_subscription_sync(event.data.object)

        return {"status": "success"}

    async def _process_checkout_completed(self, session):
        org_id = session.metadata.get("org_id")
        customer_id = session.customer
        subscription_id = session.subscription
        
        if org_id:
            await self.org_repo.sync_subscription_status(
                org_id=org_id,
                status="active",
                customer_id=customer_id,
                subscription_id=subscription_id
            )
            await self.org_repo.db.commit()

    async def _process_invoice_paid(self, invoice):
        # Find org by customer_id
        customer_id = invoice.customer
        subscription_id = invoice.subscription
        amount = invoice.amount_paid
        currency = invoice.currency
        
        r = await self.org_repo.db.execute(
            text("SELECT id FROM organizations WHERE stripe_customer_id = :cid"),
            {"cid": customer_id}
        )
        org = r.mappings().first()
        
        if org:
            org_id = str(org["id"])
            await self.repo.create_payment(
                organization_id=org_id,
                stripe_pi=invoice.payment_intent,
                stripe_invoice=invoice.id,
                amount=amount,
                currency=currency,
                status="paid"
            )
            # Update period end
            sub = stripe.Subscription.retrieve(subscription_id)
            period_end = datetime.fromtimestamp(sub.current_period_end, tz=timezone.utc)
            
            await self.org_repo.sync_subscription_status(
                org_id=org_id,
                status="active",
                period_end=period_end
            )
            
            # 3. Create Outbox Event for background notification
            outbox_item = OutboxEvent(
                event_type="billing.invoice_paid",
                payload={
                    "organization_id": org_id,
                    "amount": amount,
                    "currency": currency,
                    "stripe_invoice_id": invoice.id
                }
            )
            self.org_repo.db.add(outbox_item)
            
            await self.org_repo.db.commit()

    async def _process_subscription_sync(self, subscription):
        customer_id = subscription.customer
        status = subscription.status # active, past_due, canceled, etc.
        
        r = await self.org_repo.db.execute(
            text("SELECT id FROM organizations WHERE stripe_customer_id = :cid"),
            {"cid": customer_id}
        )
        org = r.mappings().first()
        
        if org:
            org_id = str(org["id"])
            await self.org_repo.sync_subscription_status(
                org_id=org_id,
                status=status
            )
            
            # Create Outbox Event for sync
            outbox_item = OutboxEvent(
                event_type="billing.subscription_updated",
                payload={
                    "organization_id": org_id,
                    "status": status
                }
            )
            self.org_repo.db.add(outbox_item)
            
            await self.org_repo.db.commit()

    async def request_invoice(self, org_id: str, payment_id: str, fiscal_data: dict):
        """
        Connects with FacturApi to generate CFDI.
        """
        if not facturapi:
            raise HTTPException(500, "FacturApi not configured")

        payment = await self.repo.get_payment(payment_id)
        if not payment or str(payment["organization_id"]) != org_id:
            raise HTTPException(404, "Payment not found")
        
        if payment["cfdi_status"] == "invoiced":
            raise HTTPException(400, "Invoice already generated for this payment")

        try:
            # 1. Create/Update Customer in Facturapi
            # (Simplified for now, in reality you'd search by RFC first)
            customer = facturapi.Customer.create({
                "legal_name": fiscal_data["legal_name"],
                "tax_id": fiscal_data["rfc"],
                "tax_system": fiscal_data["tax_system"],
                "email": fiscal_data.get("email"), # Could fetch from org/user
                "address": {"zip": fiscal_data["zip_code"]}
            })

            # 2. Create Invoice
            # In a real app, you'd map the Stripe items to Facturapi products
            invoice = facturapi.Invoice.create({
                "customer": customer.id,
                "items": [{
                    "quantity": 1,
                    "product": {
                        "description": "Suscripción Mediconsulta SaaS",
                        "product_key": "81111508", # Software as a service
                        "price": payment["amount"] / 100.0, # Stripe cents to decimals
                        "taxes": [{"type": "IVA", "rate": 0.16}]
                    }
                }],
                "payment_form": "03", # Transferencia
                "use": fiscal_data["use"]
            })

            # 3. Save to DB
            await self.repo.create_invoice(
                payment_id=payment_id,
                facturapi_id=invoice.id,
                uuid_sat=invoice.uuid,
                xml_url=invoice.files.xml,
                pdf_url=invoice.files.pdf
            )
            await self.repo.update_payment_cfdi_status(payment_id, "invoiced")
            await self.repo.db.commit()

            return {"status": "success", "invoice_id": invoice.id}
        except Exception as e:
            logger.error(f"FacturApi Error: {str(e)}")
            raise HTTPException(500, f"Error generating invoice: {str(e)}")
