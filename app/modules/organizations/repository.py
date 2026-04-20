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

    async def get_summary_stats(self, org_id: str):
        """Fetches high-level counts for the administrative dashboard."""
        r = await self.db.execute(
            text("""
                SELECT 
                    (SELECT COUNT(*) FROM patients WHERE organization_id = CAST(:id AS UUID)) as total_patients,
                    (SELECT COUNT(*) FROM encounters WHERE organization_id = CAST(:id AS UUID)) as total_encounters,
                    (SELECT COUNT(*) FROM clinical_sessions WHERE organization_id = CAST(:id AS UUID) AND is_active = true) as active_sessions,
                    (SELECT COUNT(*) FROM users WHERE organization_id = CAST(:id AS UUID) AND is_active = true) as total_staff
            """),
            {"id": org_id},
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
