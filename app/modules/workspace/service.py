from fastapi import HTTPException


class WorkspaceService:

    def __init__(self, repo):
        self.repo = repo

    async def encounter_workspace(
        self,
        encounter_id: str,
        doctor_id: str,
    ):

        base = await self.repo.get_base(
            encounter_id,
            doctor_id,
        )

        if not base:
            raise HTTPException(
                status_code=404,
                detail="Encounter not found or not authorized",
            )

        notes = await self.repo.get_notes(encounter_id)
        latest = await self.repo.get_latest_draft(encounter_id)
        timeline = await self.repo.get_timeline(base["patient_id"])

        return {
            "patient": {
                "id": base["patient_id"],
                "first_name": base["first_name"],
                "last_name": base["last_name"],
                "birth_date": base["birth_date"],
            },
            "encounter": {
                "id": base["encounter_id"],
                "created_at": base["created_at"],
                "status": base["encounter_status"],
            },
            "doctor": {
                "id": base["doctor_id"],
                "email": base["email"],
                "full_name": base["full_name"],
            },
            "notes": notes,
            "latest_draft": latest,
            "timeline": timeline,
        }