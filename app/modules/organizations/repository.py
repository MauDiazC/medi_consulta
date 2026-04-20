from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class OrganizationRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str):
        r = await self.db.execute(
            text("""
                INSERT INTO organizations(name, active)
                VALUES(:name, true)
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

    async def get_summary_stats(self, org_id: str, role: str, user_id: str):
        """
        Fetches role-aware statistics for the dashboard.
        Admins see clinic-wide totals.
        Doctors see their own personal stats and pending clinical tasks.
        """
        if role == "admin":
            # Global Clinic View
            query = """
                SELECT 
                    (SELECT COUNT(*) FROM patients WHERE organization_id = CAST(:oid AS UUID)) as total_patients,
                    (SELECT COUNT(*) FROM encounters WHERE organization_id = CAST(:oid AS UUID)) as total_encounters,
                    (SELECT COUNT(*) FROM clinical_sessions WHERE organization_id = CAST(:oid AS UUID) AND is_active = true) as active_sessions,
                    (SELECT COUNT(*) FROM users WHERE organization_id = CAST(:oid AS UUID) AND active = true) as total_staff,
                    'global' as scope
            """
        else:
            # Clinical Staff View (Personal Stats)
            query = """
                SELECT 
                    (SELECT COUNT(DISTINCT patient_id) FROM encounters WHERE doctor_id = CAST(:uid AS UUID)) as my_patients,
                    (SELECT COUNT(*) FROM encounters WHERE doctor_id = CAST(:uid AS UUID)) as my_total_encounters,
                    (SELECT COUNT(*) FROM clinical_notes WHERE created_by = CAST(:uid AS UUID) AND signed_at IS NULL) as pending_signatures,
                    (SELECT COUNT(*) FROM clinical_sessions WHERE user_id = CAST(:uid AS UUID) AND is_active = true) as my_active_sessions,
                    'personal' as scope
            """
        
        r = await self.db.execute(
            text(query),
            {"oid": org_id, "uid": user_id},
        )
        return r.mappings().first()

    async def update(self, org_id: str, payload):
        r = await self.db.execute(
            text("""
                UPDATE organizations
                SET name = COALESCE(:name, name),
                    address = COALESCE(:address, address),
                    phone = COALESCE(:phone, phone),
                    description = COALESCE(:description, description)
                WHERE id = CAST(:id AS UUID)
                RETURNING *
            """),
            {
                "id": org_id, 
                "name": payload.name,
                "address": payload.address,
                "phone": payload.phone,
                "description": payload.description
            },
        )
        # Commit removed for service orchestration
        return r.mappings().first()

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
