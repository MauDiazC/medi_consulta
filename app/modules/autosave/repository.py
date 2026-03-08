from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AutosaveRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_snapshot(
        self,
        note_id,
        session_id,
        data,
    ):
        await self.db.execute(
            text("""
            INSERT INTO clinical_note_drafts(
                note_id,
                session_id,
                subjective,
                objective,
                assessment,
                plan
            )
            VALUES(
                :note_id,
                :session_id,
                :subjective,
                :objective,
                :assessment,
                :plan
            )
            """),
            {
                "note_id": note_id,
                "session_id": session_id,
                **data,
            },
        )

    async def latest(self, note_id):

        r = await self.db.execute(
            text("""
            SELECT *
            FROM clinical_note_drafts
            WHERE note_id=:nid
            ORDER BY created_at DESC
            LIMIT 1
            """),
            {"nid": note_id},
        )

        return r.mappings().first()
