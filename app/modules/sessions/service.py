from fastapi import HTTPException


class SessionService:

    def __init__(self, repo):
        self.repo = repo

    async def open_session(
        self,
        encounter_id,
        user_id,
    ):
        active = await self.repo.active_session(
            encounter_id
        )

        if active and active["user_id"] != user_id:
            raise HTTPException(
                409,
                "Encounter already opened "
                "by another user",
            )

        if active:
            return active

        return await self.repo.create(
            encounter_id,
            user_id,
        )

    async def heartbeat(self, session_id):
        await self.repo.heartbeat(session_id)

    async def close(self, session_id):
        await self.repo.close(session_id)
