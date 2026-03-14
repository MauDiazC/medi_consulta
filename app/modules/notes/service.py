from fastapi import HTTPException

from app.core.audit import audit_log
from app.core.events import publish_event

from .diff import build_diff


class ClinicalNoteService:

    def __init__(self, repo):
        self.repo = repo

    async def _check_finality(self, encounter_id: str):
        """
        Hardening Gate: Block operations if encounter is sealed.
        """
        # Cross-module lookup (safe via signing module repository)
        from app.modules.notes.signing.repository import SigningRepository
        signing_repo = SigningRepository(self.repo.db)
        if await signing_repo.is_encounter_sealed(encounter_id):
            raise HTTPException(
                400, 
                "Encounter is cryptographically sealed. No modifications allowed."
            )

    async def autosave(
        self,
        encounter_id: str,
        doctor_id: str,
        fields: dict,
        expected_updated_at: str,
    ):
        await self._check_finality(encounter_id)

        draft = await self.repo.get_active_draft(
            encounter_id
        )

        if not draft:
            # Clinical Safety: Auto-provision first draft version if it doesn't exist
            new_note = await self.repo.create_new_version(
                {
                    "encounter_id": encounter_id,
                    "version": 1,
                    "subjective": fields.get("subjective", ""),
                    "objective": fields.get("objective", ""),
                    "assessment": fields.get("assessment", ""),
                    "plan": fields.get("plan", ""),
                    "created_by": doctor_id,
                }
            )
            await publish_event("note.created", {"encounter_id": encounter_id, "note_id": new_note["id"]})
            return new_note

        if str(draft["created_by"]) != str(
            doctor_id
        ):
            raise HTTPException(403, "Unauthorized")

        updated = await self.repo.autosave_update(
            draft["id"],
            fields,
            expected_updated_at,
        )

        if not updated:
            raise HTTPException(
                409,
                "Draft was modified elsewhere. Please refresh.",
            )

        await publish_event(
            "note.autosaved",
            {
                "encounter_id": encounter_id
            },
        )

        return updated

    async def finalize_version(
        self,
        encounter_id: str,
        doctor_id: str,
    ):
        await self._check_finality(encounter_id)

        draft = await self.repo.get_active_draft(
            encounter_id
        )

        if not draft:
            raise HTTPException(404)

        new_version = draft["version"] + 1

        await self.repo.deactivate_draft(
            draft["id"]
        )

        new_note = await self.repo.create_new_version(
            {
                "encounter_id": encounter_id,
                "version": new_version,
                "subjective": draft["subjective"],
                "objective": draft["objective"],
                "assessment": draft["assessment"],
                "plan": draft["plan"],
                "created_by": doctor_id,
            }
        )

        await audit_log(
            self.repo.db,
            "clinical_note",
            new_note["id"],
            "version_created",
            doctor_id,
        )

        return new_note

    async def sign(self, note_id: str, doctor_id: str, private_key_pem: bytes = None):
        """
        Orchestrates the signing of a clinical note.
        Ensures logical and cryptographic atomicity.
        """
        note, version = await self.repo.get_note_and_version(note_id)

        if not note:
            raise HTTPException(404, "Note not found")

        # Hardening Gate: Check if encounter already sealed
        await self._check_finality(str(note["encounter_id"]))

        # Idempotency check: Prevent signing if already signed
        if note["signed_at"]:
            raise HTTPException(400, "Note is already signed")

        # Validation: Only author can sign (Clinical Safety)
        author_id = note["created_by"]
        if str(author_id) != str(doctor_id):
            raise HTTPException(403, "Only the author can sign this note")

        # Delegate to Signing Module for atomic snapshotting and state change
        from app.modules.notes.signing.service import SigningApplicationService
        signing_app = SigningApplicationService(self.repo.db)

        # execute_signing manages the database transaction block (snapshot + sign + audit)
        await signing_app.execute_signing(
            note,
            version,
            str(doctor_id)
        )

        # 4) Safe Event Publication (ONLY after successful commit)
        await publish_event(
            "note.signed",
            {
                "encounter_id": str(note["encounter_id"]),
                "note_id": note_id
            },
        )

        return {"signed": True}

    async def diff_versions(
        self,
        encounter_id: str,
        v1: int,
        v2: int,
    ):

        old = await self.repo.get_version(
            encounter_id,
            v1,
        )

        new = await self.repo.get_version(
            encounter_id,
            v2,
        )

        if not old or not new:
            raise HTTPException(
                404,
                "Version not found",
            )

        return build_diff(old, new)