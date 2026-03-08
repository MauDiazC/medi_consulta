from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ContextRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, patient_id):

        r = await self.db.execute(
            text("""
            SELECT *
            FROM patient_context_memory
            WHERE patient_id=:pid
            """),
            {"pid": patient_id},
        )

        return r.mappings().first()

    async def upsert(
        self,
        patient_id,
        summary,
        medications,
        alerts,
    ):

        await self.db.execute(
            text("""
            INSERT INTO patient_context_memory(
                patient_id,
                summary,
                medications,
                alerts
            )
            VALUES(
                :pid,:s,:m,:a
            )
            ON CONFLICT (patient_id)
            DO UPDATE SET
                summary=:s,
                medications=:m,
                alerts=:a,
                updated_at=now()
            """),
            {
                "pid": patient_id,
                "s": summary,
                "m": medications,
                "a": alerts,
            },
        )
