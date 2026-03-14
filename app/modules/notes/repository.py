from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ClinicalNoteRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, note_id: str):
        r = await self.db.execute(
            text("""
            SELECT cn.*, e.organization_id
            FROM clinical_notes cn
            JOIN encounters e ON cn.encounter_id = e.id
            WHERE cn.id = :id
            """),
            {"id": note_id},
        )
        return r.mappings().first()

    async def get_active_draft(self, encounter_id: str):
        r = await self.db.execute(
            text("""
            SELECT cn.*, e.organization_id
            FROM clinical_notes cn
            JOIN encounters e ON cn.encounter_id = e.id
            WHERE cn.encounter_id = :eid
              AND cn.is_active_draft = true
              AND cn.signed_at IS NULL
            ORDER BY cn.version DESC
            LIMIT 1
            """),
            {"eid": encounter_id},
        )
        return r.mappings().first()

    async def autosave_update(
        self,
        note_id: str,
        fields: dict,
        expected_updated_at: str,
    ):
        # Professional Whitelist validation for dynamic SQL columns
        allowed_fields = {"subjective", "objective", "assessment", "plan"}
        sanitized_fields = {k: v for k, v in fields.items() if k in allowed_fields}
        
        if not sanitized_fields:
            return None

        set_clause = ", ".join(
            f"{k} = :{k}" for k in sanitized_fields.keys()
        )

        r = await self.db.execute(
            text(f"""
            UPDATE clinical_notes
            SET {set_clause},
                updated_at = now()
            WHERE id = :note_id
              AND updated_at = :expected_updated_at
            RETURNING *
            """),
            {
                **sanitized_fields,
                "note_id": note_id,
                "expected_updated_at": expected_updated_at,
            },
        )
        await self.db.commit()
        return r.mappings().first()

    async def deactivate_draft(self, note_id: str):
        await self.db.execute(
            text("""
            UPDATE clinical_notes
            SET is_active_draft = false
            WHERE id = :id
            """),
            {"id": note_id},
        )
        await self.db.commit()

    async def create_new_version(self, payload: dict):
        r = await self.db.execute(
            text("""
            INSERT INTO clinical_notes (
                encounter_id,
                version,
                subjective,
                objective,
                assessment,
                plan,
                created_by,
                is_active_draft
            )
            VALUES (
                :encounter_id,
                :version,
                :subjective,
                :objective,
                :assessment,
                :plan,
                :created_by,
                true
            )
            RETURNING *
            """),
            payload,
        )
        await self.db.commit()
        return r.mappings().first()

    async def sign(self, note_id: str):
        await self.db.execute(
            text("""
            UPDATE clinical_notes
            SET signed_at = now(),
                is_active_draft = false
            WHERE id = :id
            """),
            {"id": note_id},
        )
        await self.db.commit()

    async def get_version(
        self,
        encounter_id: str,
        version: int,
    ):
        r = await self.db.execute(
            text("""
            SELECT cn.*, e.organization_id
            FROM clinical_notes cn
            JOIN encounters e ON cn.encounter_id = e.id
            WHERE cn.encounter_id=:eid
            AND cn.version=:version
            """),
            {
                "eid": encounter_id,
                "version": version,
            },
        )
        return r.mappings().first()

    async def get_note_and_version(self, note_id: str):
        r = await self.db.execute(
            text("""
            SELECT cn.*, e.organization_id
            FROM clinical_notes cn
            JOIN encounters e ON cn.encounter_id = e.id
            WHERE cn.id = :id
            """),
            {"id": note_id},
        )
        note = r.mappings().first()
        if not note:
            return None, None
        return note, note
