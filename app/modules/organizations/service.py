from fastapi import HTTPException


class OrganizationService:

    def __init__(self, repo, user_repo):
        self.repo = repo
        self.user_repo = user_repo

    async def create(self, payload, user_id: str):
        """
        Orchestrates organization creation and bootstrap user linkage.
        """
        async with self.repo.db.begin():
            # 1. Create Organization via its authority
            org = await self.repo.create(payload.name)
            
            # 2. Assign User via User authority (Preserves Aggregate Boundary)
            await self.user_repo.assign_organization(user_id, org["id"])
            
            return org

    async def list(self, limit, offset):
        return await self.repo.list(limit, offset)

    async def get(self, org_id):
        org = await self.repo.get(org_id)
        if not org:
            raise HTTPException(404, "Organization not found")
        return org

    async def update(self, org_id, payload):
        async with self.repo.db.begin():
            org = await self.repo.update(org_id, payload)
            if not org:
                raise HTTPException(404, "Organization not found")
            return org

    async def deactivate(self, org_id):
        async with self.repo.db.begin():
            await self.repo.deactivate(org_id)

    async def activate(self, org_id):
        async with self.repo.db.begin():
            await self.repo.activate(org_id)
