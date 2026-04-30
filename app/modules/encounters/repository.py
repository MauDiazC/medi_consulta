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
                    CAST(:session AS UUID),
                    CAST(:patient AS UUID),
                    CAST(:org AS UUID),
                    CAST(:doctor AS UUID),
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
                SELECT e.*, 
                       p.first_name || ' ' || p.last_name as patient_name,
                       u.full_name as doctor_name
                FROM encounters e
                JOIN patients p ON e.patient_id = p.id
                JOIN users u ON e.doctor_id = u.id
                WHERE e.id = CAST(:id AS UUID)
                AND e.organization_id = CAST(:org AS UUID)
            """),
            {"id": encounter_id, "org": org},
        )
        return r.mappings().first()

    async def list(self, org, limit, offset, doctor_ids: list[str] | None = None):
        query = """
            SELECT e.*, 
                   p.first_name || ' ' || p.last_name as patient_name,
                   u.full_name as doctor_name
            FROM encounters e
            JOIN patients p ON e.patient_id = p.id
            JOIN users u ON e.doctor_id = u.id
            WHERE e.organization_id = CAST(:org AS UUID)
        """
        params = {"org": org, "limit": limit, "offset": offset}
        
        if doctor_ids is not None:
            if not doctor_ids:
                return []
            query += " AND e.doctor_id = ANY(:doctor_ids)"
            params["doctor_ids"] = doctor_ids

        query += " ORDER BY e.created_at DESC LIMIT :limit OFFSET :offset"
        
        r = await self.db.execute(text(query), params)
        return r.mappings().all()

    async def list_by_patient(self, patient_id, org, limit, offset, doctor_ids: list[str] | None = None):
        query = """
            SELECT e.*, 
                   p.first_name || ' ' || p.last_name as patient_name,
                   u.full_name as doctor_name
            FROM encounters e
            JOIN patients p ON e.patient_id = p.id
            JOIN users u ON e.doctor_id = u.id
            WHERE e.patient_id = CAST(:patient AS UUID)
            AND e.organization_id = CAST(:org AS UUID)
        """
        params = {"patient": patient_id, "org": org, "limit": limit, "offset": offset}

        if doctor_ids is not None:
            if not doctor_ids:
                return []
            query += " AND e.doctor_id = ANY(:doctor_ids)"
            params["doctor_ids"] = doctor_ids

        query += " ORDER BY e.created_at DESC LIMIT :limit OFFSET :offset"

        r = await self.db.execute(text(query), params)
        return r.mappings().all()

    async def list_by_doctor(self, doctor_id, org, limit, offset):
        r = await self.db.execute(
            text("""
                SELECT e.*, 
                       p.first_name || ' ' || p.last_name as patient_name,
                       u.full_name as doctor_name
                FROM encounters e
                JOIN patients p ON e.patient_id = p.id
                JOIN users u ON e.doctor_id = u.id
                WHERE e.doctor_id = CAST(:doctor AS UUID)
                AND e.organization_id = CAST(:org AS UUID)
                ORDER BY e.created_at DESC
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

    async def list_by_session(self, session_id, org, limit, offset, doctor_ids: list[str] | None = None):
        query = """
            SELECT e.*, 
                   p.first_name || ' ' || p.last_name as patient_name,
                   u.full_name as doctor_name
            FROM encounters e
            JOIN patients p ON e.patient_id = p.id
            JOIN users u ON e.doctor_id = u.id
            WHERE e.clinical_session_id = CAST(:session AS UUID)
            AND e.organization_id = CAST(:org AS UUID)
        """
        params = {"session": session_id, "org": org, "limit": limit, "offset": offset}

        if doctor_ids is not None:
            if not doctor_ids:
                return []
            query += " AND e.doctor_id = ANY(:doctor_ids)"
            params["doctor_ids"] = doctor_ids

        query += " ORDER BY e.created_at DESC LIMIT :limit OFFSET :offset"

        r = await self.db.execute(text(query), params)
        return r.mappings().all()

    async def update(self, encounter_id, org, payload):
        r = await self.db.execute(
            text("""
                UPDATE encounters
                SET reason = COALESCE(:reason, reason)
                WHERE id = CAST(:id AS UUID) AND organization_id = CAST(:org AS UUID)
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
                WHERE id = CAST(:id AS UUID) AND organization_id = CAST(:org AS UUID)
            """),
            {"id": encounter_id, "org": org},
        )
        await self.db.commit()

    async def reassign_doctor(self, encounter_id: str, org: str, new_doctor_id: str):
        r = await self.db.execute(
            text("""
                UPDATE encounters
                SET doctor_id = CAST(:doctor AS UUID)
                WHERE id = CAST(:id AS UUID) AND organization_id = CAST(:org AS UUID)
                RETURNING *
            """),
            {
                "id": encounter_id,
                "org": org,
                "doctor": new_doctor_id,
            },
        )
        await self.db.commit()
        return r.mappings().first()
