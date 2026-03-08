from fastapi import HTTPException


class AutosaveService:

    def __init__(self, repo, session_repo):
        self.repo = repo
        self.session_repo = session_repo

    async def autosave(
        self,
        note_id,
        session_id,
        payload,
    ):
        session = await self.session_repo.active_session(
            payload["encounter_id"]
        )

        if not session:
            raise HTTPException(
                409,
                "No active session"
            )

        await self.repo.save_snapshot(
            note_id,
            session_id,
            payload,
        )

        return {"saved": True}

    async def recover(self, note_id):
        return await self.repo.latest(note_id)
