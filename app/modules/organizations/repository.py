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
                WHERE active=true
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
                WHERE id=:id
            """),
            {"id": org_id},
        )
        return r.mappings().first()

    async def update(self, org_id: str, payload):
        r = await self.db.execute(
            text("""
                UPDATE organizations
                SET name = COALESCE(:name, name)
                WHERE id=:id
                RETURNING *
            """),
            {"id": org_id, "name": payload.name},
        )
        # Commit removed for service orchestration
        return r.mappings().first()

    async def deactivate(self, org_id: str):
        await self.db.execute(
            text("""
                UPDATE organizations
                SET active=false
                WHERE id=:id
            """),
            {"id": org_id},
        )
        # Commit removed for service orchestration
