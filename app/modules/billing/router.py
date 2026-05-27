from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.core.database import get_db
from app.core.permissions import require_role
from app.modules.organizations.repository import OrganizationRepository

from .repository import BillingRepository
from .schemas import CheckoutRequest, CheckoutResponse, InvoiceRequest, PaymentDTO
from .service import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])


def get_service(db=Depends(get_db)):
    return BillingService(BillingRepository(db), OrganizationRepository(db))


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    payload: CheckoutRequest,
    user=Depends(require_role("admin")),
    s=Depends(get_service),
):
    """
    Initiates a Stripe Checkout Session.
    Only admins can subscribe their organization.
    """
    # URLs for the frontend
    success_url = (
        "https://mediconsulta.app/billing/success?session_id={CHECKOUT_SESSION_ID}"
    )
    cancel_url = "https://mediconsulta.app/billing/cancel"

    url = await s.create_checkout_session(
        org_id=user["org"],
        plan_code=payload.plan_code,
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return {"checkout_url": url}


@router.get("/portal")
async def get_portal(user=Depends(require_role("admin")), s=Depends(get_service)):
    """
    Returns the Stripe Customer Portal URL.
    """
    return {
        "portal_url": await s.create_portal_session(
            user["org"], "https://mediconsulta.app/billing"
        )
    }


@router.get("/history", response_model=list[PaymentDTO])
async def get_payment_history(
    user=Depends(require_role("admin")), s=Depends(get_service)
):
    """
    Lists past payments for the organization.
    """
    return await s.repo.list_payments_by_org(user["org"])


@router.post("/payments/{payment_id}/request-invoice")
async def request_invoice(
    payment_id: str,
    payload: InvoiceRequest,
    user=Depends(require_role("admin")),
    s=Depends(get_service),
):
    """
    Trigger FacturApi CFDI generation on demand.
    """
    return await s.request_invoice(user["org"], payment_id, payload.dict())


@router.post("/webhook")
async def stripe_webhook(
    request: Request, stripe_signature: str = Header(None), s=Depends(get_service)
):
    """
    Stripe Webhook Listener.
    """
    if not stripe_signature:
        raise HTTPException(400, "Missing signature")

    payload = await request.body()
    try:
        return await s.handle_webhook(payload.decode("utf-8"), stripe_signature)
    except ValueError as e:
        raise HTTPException(400, str(e))
