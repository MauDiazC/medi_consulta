from datetime import datetime
import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class OrganizationRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str):
        r = await self.db.execute(
            text("""
                INSERT INTO organizations(name, active, settings)
                VALUES(:name, true, '{}')
                RETURNING *
            """),
            {"name": name},
        )
        # Commit removed for service orchestration
        return r.mappings().first()

    async def list(self, limit: int, offset: int):
        r = await self.db.execute(
            text("""
                SELECT *
                FROM organizations
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"limit": limit, "offset": offset},
        )
        return r.mappings().all()

    async def get(self, org_id: str):
        r = await self.db.execute(
            text("""
                SELECT *
                FROM organizations
                WHERE id = CAST(:id AS UUID)
            """),
            {"id": org_id},
        )
        return r.mappings().first()

    async def get_summary_stats(
        self, 
        org_id: str, 
        role: str, 
        user_id: str,
        start_date: str | None = None,
        end_date: str | None = None
    ):
        """
        Fetches role-aware statistics for the dashboard.
        Admins see clinic-wide totals.
        Doctors see their own historical performance and current pending tasks.
        Includes optional date range filtering.
        """
        date_filter = ""
        params = {"oid": org_id, "uid": user_id}

        if start_date:
            try:
                # Handle YYYY-MM-DD
                params["start_date"] = datetime.strptime(start_date, "%Y-%m-%d")
                date_filter += " AND created_at >= :start_date"
            except ValueError:
                pass # Or raise error
        
        if end_date:
            try:
                params["end_date"] = datetime.strptime(end_date, "%Y-%m-%d")
                date_filter += " AND created_at <= :end_date"
            except ValueError:
                pass

        if role == "admin":
            # Global Clinic View
            query = f"""
                SELECT 
                    (SELECT COUNT(*) FROM patients WHERE organization_id = CAST(:oid AS UUID)) as total_patients,
                    (SELECT COUNT(*) FROM encounters WHERE organization_id = CAST(:oid AS UUID) {date_filter}) as total_encounters,
                    (SELECT COUNT(*) FROM clinical_sessions WHERE organization_id = CAST(:oid AS UUID) AND is_active = true) as active_sessions,
                    (SELECT COUNT(*) FROM users WHERE organization_id = CAST(:oid AS UUID) AND active = true) as total_staff,
                    'global' as scope
            """
        else:
            # Clinical Staff View (Personal Stats)
            query = f"""
                SELECT 
                    (
                        SELECT COUNT(DISTINCT patient_id) 
                        FROM encounters 
                        WHERE doctor_id = CAST(:uid AS UUID) 
                        AND organization_id = CAST(:oid AS UUID)
                        {date_filter}
                    ) as my_patients,
                    (
                        SELECT COUNT(*) 
                        FROM encounters 
                        WHERE doctor_id = CAST(:uid AS UUID) 
                        AND organization_id = CAST(:oid AS UUID)
                        {date_filter}
                    ) as my_total_encounters,
                    (
                        SELECT COUNT(DISTINCT encounter_id) 
                        FROM clinical_notes cn1
                        WHERE cn1.created_by = CAST(:uid AS UUID) 
                        AND cn1.signed_at IS NULL
                        AND EXISTS (
                            SELECT 1 FROM encounters e 
                            WHERE e.id = cn1.encounter_id 
                            AND e.organization_id = CAST(:oid AS UUID)
                        )
                        AND NOT EXISTS (
                            SELECT 1 FROM clinical_notes cn2 
                            WHERE cn2.encounter_id = cn1.encounter_id 
                            AND cn2.signed_at IS NOT NULL
                        )
                        {date_filter.replace('created_at', 'cn1.created_at')}
                    ) as pending_signatures,
                    (
                        SELECT COUNT(*) 
                        FROM clinical_sessions 
                        WHERE user_id = CAST(:uid AS UUID) 
                        AND is_active = true
                        AND organization_id = CAST(:oid AS UUID)
                    ) as my_active_sessions,
                    'personal' as scope
            """
        
        r = await self.db.execute(
            text(query),
            params,
        )
        return r.mappings().first()

    async def update(self, org_id: str, payload):
        settings_json = json.dumps(payload.settings) if payload.settings is not None else None
        r = await self.db.execute(
            text("""
                UPDATE organizations
                SET name = COALESCE(:name, name),
                    address = COALESCE(:address, address),
                    phone = COALESCE(:phone, phone),
                    description = COALESCE(:description, description),
                    logo_url = COALESCE(:logo_url, logo_url),
                    settings = COALESCE(CAST(:settings AS JSONB), settings),
                    stripe_customer_id = COALESCE(:stripe_customer_id, stripe_customer_id),
                    stripe_subscription_id = COALESCE(:stripe_subscription_id, stripe_subscription_id),
                    subscription_status = COALESCE(:subscription_status, subscription_status),
                    subscription_period_end = COALESCE(:subscription_period_end, subscription_period_end)
                WHERE id = CAST(:id AS UUID)
                RETURNING *
            """),
            {
                "id": org_id, 
                "name": payload.name,
                "address": payload.address,
                "phone": payload.phone,
                "description": payload.description,
                "logo_url": payload.logo_url,
                "settings": settings_json,
                "stripe_customer_id": payload.stripe_customer_id,
                "stripe_subscription_id": payload.stripe_subscription_id,
                "subscription_status": payload.subscription_status,
                "subscription_period_end": payload.subscription_period_end
            },
        )
        # Commit removed for service orchestration
        return r.mappings().first()

    async def sync_subscription_status(
        self, 
        org_id: str, 
        status: str, 
        customer_id: str | None = None, 
        subscription_id: str | None = None,
        period_end: datetime | None = None
    ):
        """
        Specialized atomic update for Stripe webhooks.
        """
        await self.db.execute(
            text("""
                UPDATE organizations
                SET subscription_status = :status,
                    stripe_customer_id = COALESCE(:customer_id, stripe_customer_id),
                    stripe_subscription_id = COALESCE(:sub_id, stripe_subscription_id),
                    subscription_period_end = COALESCE(:period_end, subscription_period_end)
                WHERE id = CAST(:id AS UUID)
            """),
            {
                "id": org_id,
                "status": status,
                "customer_id": customer_id,
                "sub_id": subscription_id,
                "period_end": period_end
            }
        )

    async def deactivate(self, org_id: str):
        await self.db.execute(
            text("""
                UPDATE organizations
                SET active=false
                WHERE id = CAST(:id AS UUID)
            """),
            {"id": org_id},
        )
        # Commit removed for service orchestration

    async def activate(self, org_id: str):
        """Re-enables an organization."""
        await self.db.execute(
            text("""
                UPDATE organizations
                SET active=true
                WHERE id = CAST(:id AS UUID)
            """),
            {"id": org_id},
        )
        # Commit removed for service orchestration

    async def hard_delete(self, org_id: str):
        """DANGER: Physical deletion. Use only for dev/testing."""
        await self.db.execute(
            text("DELETE FROM organizations WHERE id = CAST(:id AS UUID)"),
            {"id": org_id}
        )
        await self.db.commit()
