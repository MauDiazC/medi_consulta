class ClinicalSessionService:

    def __init__(self, repo):
        self._repo = repo

    async def create(self, payload, org_id):
        return await self._repo.create(
            payload.name,
            org_id,
        )