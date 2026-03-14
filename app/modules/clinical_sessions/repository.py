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
                    organization_id
                )
                VALUES (
                    :name,
                    :organization_id
                )
                RETURNING id, name, organization_id
            """),
            {
                "name": name,
                "organization_id": organization_id,
            },
        )

        await self._db.commit()
        return result.mappings().first()