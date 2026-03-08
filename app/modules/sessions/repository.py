from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SessionRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def active_session(self, encounter_id):
        r = await self.db.execute(text("""
        SELECT *
        FROM encounter_sessions
        WHERE encounter_id=:eid
        AND status='active'
        """), {"eid": encounter_id})

        return r.mappings().first()

    async def create(self, encounter_id, user_id):
        r = await self.db.execute(text("""
        INSERT INTO encounter_sessions(
            encounter_id,user_id
        )
        VALUES(:eid,:uid)
        RETURNING *
        """), {"eid": encounter_id,
               "uid": user_id})

        return r.mappings().first()

    async def heartbeat(self, session_id):
        await self.db.execute(text("""
        UPDATE encounter_sessions
        SET last_activity=now()
        WHERE id=:id
        """), {"id": session_id})

    async def close(self, session_id):
        await self.db.execute(text("""
        UPDATE encounter_sessions
        SET status='completed',
            closed_at=now()
        WHERE id=:id
        """), {"id": session_id})
