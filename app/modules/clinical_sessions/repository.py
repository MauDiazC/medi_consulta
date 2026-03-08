from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ClinicalSessionRepository:

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(
        self,
        patient_id: str,
        organization_id: str,
    ):
        result = await self._db.execute(
            text("""
                INSERT INTO clinical_sessions (
                    patient_id,
                    organization_id,
                    status
                )
                VALUES (
                    :patient_id,
                    :organization_id,
                    'active'
                )
                RETURNING id, patient_id, organization_id, status
            """),
            {
                "patient_id": patient_id,
                "organization_id": organization_id,
            },
        )

        await self._db.commit()
        return result.mappings().first()