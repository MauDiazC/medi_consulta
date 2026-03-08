from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class WorkspaceRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_base(self, encounter_id: str, doctor_id: str):

        r = await self.db.execute(
            text("""
            SELECT
                e.id as encounter_id,
                e.created_at,
                e.status as encounter_status,

                p.id as patient_id,
                p.first_name,
                p.last_name,
                p.birth_date,

                u.id as doctor_id,
                u.email,
                u.full_name

            FROM encounters e
            JOIN patients p ON p.id = e.patient_id
            JOIN users u ON u.id = e.clinician_id

            WHERE e.id = :encounter_id
              AND e.clinician_id = :doctor_id
            """),
            {
                "encounter_id": encounter_id,
                "doctor_id": doctor_id,
            },
        )

        return r.mappings().first()

    async def get_notes(self, encounter_id: str):

        r = await self.db.execute(
            text("""
            SELECT *,
                CASE
                    WHEN signed_at IS NULL THEN 'draft'
                    ELSE 'signed'
                END as status
            FROM clinical_notes
            WHERE encounter_id = :eid
            ORDER BY version DESC
            """),
            {"eid": encounter_id},
        )

        return r.mappings().all()

    async def get_latest_draft(self, encounter_id: str):

        r = await self.db.execute(
            text("""
            SELECT *
            FROM clinical_notes
            WHERE encounter_id = :eid
              AND signed_at IS NULL
            ORDER BY version DESC
            LIMIT 1
            """),
            {"eid": encounter_id},
        )

        return r.mappings().first()

    async def get_timeline(self, patient_id: str):

        r = await self.db.execute(
            text("""
            SELECT
                e.id as encounter_id,
                e.created_at,
                e.status as encounter_status,

                MAX(n.version) as latest_version,

                MAX(
                    CASE WHEN n.signed_at IS NOT NULL THEN n.id END
                ) as latest_signed_note_id

            FROM encounters e
            LEFT JOIN clinical_notes n
              ON n.encounter_id = e.id

            WHERE e.patient_id = :pid
            GROUP BY e.id
            ORDER BY e.created_at DESC
            """),
            {"pid": patient_id},
        )

        return r.mappings().all()