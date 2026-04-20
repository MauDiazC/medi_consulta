from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ClinicalNoteRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, note_id: str, organization_id: str):
        """Secure get by ID and Organization."""
        r = await self.db.execute(
            text("""
            SELECT cn.*, e.organization_id
            FROM clinical_notes cn
            JOIN encounters e ON cn.encounter_id = e.id
            WHERE cn.id = CAST(:id AS UUID) AND e.organization_id = CAST(:org_id AS UUID)
            """),
            {"id": note_id, "org_id": organization_id},
        )
        return r.mappings().first()

    async def get_active_draft(self, encounter_id: str, organization_id: str):
        """Secure draft fetch by encounter and organization."""
        r = await self.db.execute(
            text("""
            SELECT cn.*, e.organization_id
            FROM clinical_notes cn
            JOIN encounters e ON cn.encounter_id = e.id
            WHERE cn.encounter_id = CAST(:eid AS UUID)
              AND e.organization_id = CAST(:org_id AS UUID)
              AND cn.is_active_draft = true
              AND cn.signed_at IS NULL
            ORDER BY cn.version DESC
            LIMIT 1
            """),
            {"eid": encounter_id, "org_id": organization_id},
        )
        return r.mappings().first()

    async def autosave_update(
        self,
        note_id: str,
        organization_id: str,
        fields: dict,
        expected_updated_at: str,
    ):
        """Secure update validating the organization ownership via join."""
        allowed_fields = {"subjective", "objective", "assessment", "plan"}
        sanitized_fields = {k: v for k, v in fields.items() if k in allowed_fields}
        
        if not sanitized_fields:
            return None

        set_clause = ", ".join(
            f"{k} = :{k}" for k in sanitized_fields.keys()
        )

        # UPDATE with JOIN or subquery to ensure multi-tenancy
        r = await self.db.execute(
            text(f"""
            UPDATE clinical_notes
            SET {set_clause},
                updated_at = now()
            WHERE id = CAST(:note_id AS UUID)
              AND updated_at = :expected_updated_at
              AND id IN (
                  SELECT cn.id FROM clinical_notes cn
                  JOIN encounters e ON cn.encounter_id = e.id
                  WHERE e.organization_id = CAST(:org_id AS UUID)
              )
            RETURNING *
            """),
            {
                **sanitized_fields,
                "note_id": note_id,
                "org_id": organization_id,
                "expected_updated_at": expected_updated_at,
            },
        )
        await self.db.commit()
        return r.mappings().first()

    async def deactivate_draft(self, note_id: str, organization_id: str):
        """Deactivate validating organization."""
        await self.db.execute(
            text("""
            UPDATE clinical_notes
            SET is_active_draft = false
            WHERE id = CAST(:id AS UUID)
            AND id IN (
                SELECT cn.id FROM clinical_notes cn
                JOIN encounters e ON cn.encounter_id = e.id
                WHERE e.organization_id = CAST(:org_id AS UUID)
            )
            """),
            {"id": note_id, "org_id": organization_id},
        )
        await self.db.commit()

    async def create_new_version(self, payload: dict, organization_id: str):
        """Secure insert ensuring encounter belongs to the same organization."""
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
            SELECT CAST(:encounter_id AS UUID), :version, :subjective, :objective, :assessment, :plan, CAST(:created_by AS UUID), true
            FROM encounters e
            WHERE e.id = CAST(:encounter_id AS UUID) AND e.organization_id = CAST(:org_id AS UUID)
            RETURNING *
            """),
            {**payload, "org_id": organization_id},
        )
        await self.db.commit()
        return r.mappings().first()

    async def sign(self, note_id: str, organization_id: str):
        """Secure sign validating organization and closing the draft."""
        await self.db.execute(
            text("""
            UPDATE clinical_notes
            SET signed_at = now(),
                is_active_draft = false
            WHERE id = CAST(:id AS UUID)
            AND id IN (
                SELECT cn.id FROM clinical_notes cn
                JOIN encounters e ON cn.encounter_id = e.id
                WHERE e.organization_id = CAST(:org_id AS UUID)
            )
            """),
            {"id": note_id, "org_id": organization_id},
        )
        await self.db.commit()

    async def supersede_previous_versions(self, encounter_id: str, current_note_id: str):
        """
        Legal Maintenance: Marks all previous versions of an encounter as superseded.
        Ensures only the authoritative (signed or latest) version remains in focus.
        """
        await self.db.execute(
            text("""
                UPDATE clinical_notes
                SET is_active_draft = false,
                    updated_at = now()
                WHERE encounter_id = CAST(:eid AS UUID)
                  AND id != CAST(:current_id AS UUID)
                  AND signed_at IS NULL
            """),
            {"eid": encounter_id, "current_id": current_note_id}
        )
        await self.db.commit()

    async def get_version(
        self,
        encounter_id: str,
        version: int,
        organization_id: str
    ):
        """Secure fetch by version and organization."""
        r = await self.db.execute(
            text("""
            SELECT cn.*, e.organization_id
            FROM clinical_notes cn
            JOIN encounters e ON cn.encounter_id = e.id
            WHERE cn.encounter_id = CAST(:eid AS UUID)
            AND cn.version = :version
            AND e.organization_id = CAST(:org_id AS UUID)
            """),
            {
                "eid": encounter_id,
                "version": version,
                "org_id": organization_id
            },
        )
        return r.mappings().first()

    async def list_by_encounter(self, encounter_id: str, organization_id: str):
        """Lists all versions of notes for a specific encounter, ensuring org isolation."""
        r = await self.db.execute(
            text("""
            SELECT cn.*
            FROM clinical_notes cn
            JOIN encounters e ON cn.encounter_id = e.id
            WHERE cn.encounter_id = CAST(:eid AS UUID)
              AND e.organization_id = CAST(:org_id AS UUID)
            ORDER BY cn.version DESC
            """),
            {"eid": encounter_id, "org_id": organization_id},
        )
        return r.mappings().all()
