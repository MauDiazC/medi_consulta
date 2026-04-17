from fastapi import HTTPException


class ClinicalSessionService:

    def __init__(self, repo):
        self._repo = repo

    async def create(self, payload, org_id):
        return await self._repo.create(
            payload.name,
            org_id,
        )

    async def list(self, org_id, limit, offset):
        return await self._repo.list(org_id, limit, offset)

    async def get(self, session_id, org_id):
        session = await self._repo.get(session_id, org_id)
        if not session:
            raise HTTPException(status_code=404, detail="Sesión clínica no encontrada")
        return session

    async def deactivate(self, session_id, org_id):
        await self._repo.deactivate(session_id, org_id)
        return {"status": "deactivated"}