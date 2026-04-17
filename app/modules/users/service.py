from fastapi import HTTPException

from app.core.security import hash_password


class UserService:

    def __init__(self, repo):
        self.repo = repo

    async def create(self, payload):
        return await self.repo.create(
            payload.email,
            hash_password(payload.password),
            payload.full_name,
            payload.role,
            payload.organization_id,
        )

    async def list(self, org, limit, offset):
        return await self.repo.list(org, limit, offset)

    async def get(self, user_id, org):
        user = await self.repo.get(user_id, org)
        if not user:
            raise HTTPException(404, "User not found")
        return user

    async def update(self, user_id, org, payload):
        user = await self.repo.update(user_id, org, payload)
        if not user:
            raise HTTPException(404, "User not found")
        return user

    async def deactivate(self, user_id, org):
        await self.repo.deactivate(user_id, org)