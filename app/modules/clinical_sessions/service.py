from fastapi import HTTPException


class ClinicalSessionService:

    def __init__(self, repo):
        self._repo = repo

    async def create(self, payload, org_id, user_id):
        return await self._repo.create(
            payload.name,
            org_id,
            user_id,
        )

    async def list(self, org_id, limit, offset, is_active: bool = None, authorized_doctor_ids: list[str] = None):
        return await self._repo.list(org_id, limit, offset, is_active, authorized_doctor_ids)

    async def get(self, session_id, org_id, authorized_doctor_ids: list[str] = None):
        session = await self._repo.get(session_id, org_id, authorized_doctor_ids)
        if not session:
            raise HTTPException(status_code=404, detail="Sesión clínica no encontrada")
        return session

    async def get_encounters(self, session_id, org_id, authorized_doctor_ids: list[str] = None):
        # First validate access to the session
        await self.get(session_id, org_id, authorized_doctor_ids)
        return await self._repo.get_encounters(session_id, org_id)

    async def deactivate(self, session_id, org_id):
        await self._repo.deactivate(session_id, org_id)
        return {"status": "deactivated"}

    async def close(self, session_id, org_id):
        """Semantic close with timestamp."""
        await self._repo.close(session_id, org_id)
        return {"status": "closed"}

    async def activate(self, session_id, org_id):
        await self._repo.activate(session_id, org_id)
        return {"status": "activated"}