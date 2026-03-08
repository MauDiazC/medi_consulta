from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class EncounterRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload, org, doctor_id):

        r = await self.db.execute(
            text("""
                INSERT INTO encounters(
                    clinical_session_id,
                    patient_id,
                    organization_id,
                    doctor_id,
                    reason,
                    status
                )
                VALUES(
                    :session,
                    :patient,
                    :org,
                    :doctor,
                    :reason,
                    'open'
                )
                RETURNING *
            """),
            {
                "session": payload.clinical_session_id,
                "patient": payload.patient_id,
                "org": org,
                "doctor": doctor_id,
                "reason": payload.reason,
            },
        )

        await self.db.commit()
        return r.mappings().first()

    async def get(self, encounter_id, org):
        r = await self.db.execute(
            text("""
                SELECT *
                FROM encounters
                WHERE id=:id
                AND organization_id=:org
            """),
            {"id": encounter_id, "org": org},
        )
        return r.mappings().first()

    async def list(self, org, limit, offset):
        r = await self.db.execute(
            text("""
                SELECT *
                FROM encounters
                WHERE organization_id=:org
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"org": org, "limit": limit, "offset": offset},
        )
        return r.mappings().all()

    async def list_by_patient(self, patient_id, org, limit, offset):
        r = await self.db.execute(
            text("""
                SELECT *
                FROM encounters
                WHERE patient_id=:patient
                AND organization_id=:org
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {
                "patient": patient_id,
                "org": org,
                "limit": limit,
                "offset": offset,
            },
        )
        return r.mappings().all()

    async def list_by_doctor(self, doctor_id, org, limit, offset):
        r = await self.db.execute(
            text("""
                SELECT *
                FROM encounters
                WHERE doctor_id=:doctor
                AND organization_id=:org
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {
                "doctor": doctor_id,
                "org": org,
                "limit": limit,
                "offset": offset,
            },
        )
        return r.mappings().all()

    async def list_by_session(self, session_id, org, limit, offset):
        r = await self.db.execute(
            text("""
                SELECT *
                FROM encounters
                WHERE clinical_session_id=:session
                AND organization_id=:org
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {
                "session": session_id,
                "org": org,
                "limit": limit,
                "offset": offset,
            },
        )
        return r.mappings().all()

    async def update(self, encounter_id, org, payload):
        r = await self.db.execute(
            text("""
                UPDATE encounters
                SET reason = COALESCE(:reason, reason)
                WHERE id=:id AND organization_id=:org
                RETURNING *
            """),
            {
                "id": encounter_id,
                "org": org,
                "reason": payload.reason,
            },
        )
        await self.db.commit()
        return r.mappings().first()

    async def close(self, encounter_id, org):
        await self.db.execute(
            text("""
                UPDATE encounters
                SET status='closed'
                WHERE id=:id AND organization_id=:org
            """),
            {"id": encounter_id, "org": org},
        )
        await self.db.commit()