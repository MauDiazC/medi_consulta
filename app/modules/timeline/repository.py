from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class TimelineRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def patient_timeline(self, patient_id):
        r = await self.db.execute(
            text("""
            SELECT
                e.id as encounter_id,
                e.created_at,
                n.id as note_id,
                n.status
            FROM encounters e
            LEFT JOIN clinical_notes n
            ON n.encounter_id=e.id
            WHERE e.patient_id=:pid
            ORDER BY e.created_at DESC
            """),
            {"pid": patient_id},
        )
        return r.mappings().all()
