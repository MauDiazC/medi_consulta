from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class CopilotRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, note_id, session_id, suggestions):

        for s in suggestions:
            await self.db.execute(
                text("""
                INSERT INTO ai_copilot_suggestions(
                    note_id,
                    session_id,
                    suggestion_type,
                    content
                )
                VALUES(
                    :note_id,
                    :session_id,
                    :type,
                    :content
                )
                """),
                {
                    "note_id": note_id,
                    "session_id": session_id,
                    "type": s["type"],
                    "content": s["content"],
                },
            )

    async def latest(self, note_id):

        r = await self.db.execute(
            text("""
            SELECT *
            FROM ai_copilot_suggestions
            WHERE note_id=:nid
            ORDER BY created_at DESC
            LIMIT 10
            """),
            {"nid": note_id},
        )

        return r.mappings().all()
