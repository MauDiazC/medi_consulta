import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class BillingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment(
        self,
        organization_id: str,
        stripe_pi: str,
        stripe_invoice: str,
        amount: int,
        currency: str,
        status: str,
    ):
        r = await self.db.execute(
            text("""
                INSERT INTO billing_payments (organization_id, stripe_payment_intent_id, stripe_invoice_id, amount, currency, status)
                VALUES (CAST(:oid AS UUID), :pi, :inv, :amt, :cur, :status)
                RETURNING *
            """),
            {
                "oid": organization_id,
                "pi": stripe_pi,
                "inv": stripe_invoice,
                "amt": amount,
                "cur": currency,
                "status": status,
            },
        )
        return r.mappings().first()

    async def get_payment(self, payment_id: str):
        r = await self.db.execute(
            text("SELECT * FROM billing_payments WHERE id = CAST(:id AS UUID)"),
            {"id": payment_id},
        )
        return r.mappings().first()

    async def update_payment_cfdi_status(self, payment_id: str, status: str):
        await self.db.execute(
            text(
                "UPDATE billing_payments SET cfdi_status = :status WHERE id = CAST(:id AS UUID)"
            ),
            {"id": payment_id, "status": status},
        )

    async def create_invoice(
        self,
        payment_id: str,
        facturapi_id: str,
        uuid_sat: str,
        xml_url: str,
        pdf_url: str,
    ):
        r = await self.db.execute(
            text("""
                INSERT INTO billing_invoices (payment_id, facturapi_id, uuid_sat, xml_url, pdf_url, status)
                VALUES (CAST(:pid AS UUID), :fid, :sat, :xml, :pdf, 'valid')
                RETURNING *
            """),
            {
                "pid": payment_id,
                "fid": facturapi_id,
                "sat": uuid_sat,
                "xml": xml_url,
                "pdf": pdf_url,
            },
        )
        return r.mappings().first()

    async def log_webhook(self, event_type: str, payload: dict):
        await self.db.execute(
            text("""
                INSERT INTO billing_webhook_logs (event_type, payload, processed)
                VALUES (:type, CAST(:payload AS JSONB), false)
            """),
            {"type": event_type, "payload": json.dumps(payload)},
        )
        await self.db.commit()

    async def list_payments_by_org(self, organization_id: str):
        r = await self.db.execute(
            text("""
                SELECT * FROM billing_payments
                WHERE organization_id = CAST(:oid AS UUID)
                ORDER BY created_at DESC
            """),
            {"oid": organization_id},
        )
        return r.mappings().all()
