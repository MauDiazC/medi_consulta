from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ClinicalSessionRepository:

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(
        self,
        name: str,
        organization_id: str,
    ):
        result = await self._db.execute(
            text("""
                INSERT INTO clinical_sessions (
                    name,
                    organization_id,
                    is_active
                )
                VALUES (
                    :name,
                    CAST(:organization_id AS UUID),
                    true
                )
                RETURNING *
            """),
            {
                "name": name,
                "organization_id": organization_id,
            },
        )

        await self._db.commit()
        return result.mappings().first()

    async def list(self, org_id: str, limit: int = 10, offset: int = 0):
        """List sessions for an organization."""
        r = await self._db.execute(
            text("""
                SELECT * FROM clinical_sessions
                WHERE organization_id = CAST(:org_id AS UUID)
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"org_id": org_id, "limit": limit, "offset": offset}
        )
        return r.mappings().all()

    async def get(self, session_id: str, org_id: str):
        """Get a specific session validating organization."""
        r = await self._db.execute(
            text("""
                SELECT * FROM clinical_sessions
                WHERE id = CAST(:id AS UUID) AND organization_id = CAST(:org_id AS UUID)
            """),
            {"id": session_id, "org_id": org_id}
        )
        return r.mappings().first()

    async def deactivate(self, session_id: str, org_id: str):
        """Close/deactivate a clinical session."""
        await self._db.execute(
            text("""
                UPDATE clinical_sessions
                SET is_active = false
                WHERE id = CAST(:id AS UUID) AND organization_id = CAST(:org_id AS UUID)
            """),
            {"id": session_id, "org_id": org_id}
        )
        await self._db.commit()