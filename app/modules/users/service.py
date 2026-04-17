from fastapi import HTTPException, status

from app.core.security import hash_password


class UserService:

    def __init__(self, repo):
        self.repo = repo

    async def create(self, payload):
        # 1. Check if email already exists
        existing = await self.repo.get_by_email(payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El correo {payload.email} ya está registrado."
            )

        user = await self.repo.create(
            payload.email,
            hash_password(payload.password),
            payload.full_name,
            payload.role,
            payload.organization_id,
        )
        
        # 2. Persist to DB
        await self.repo.db.commit()
        return user

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
        
        await self.repo.db.commit()
        return user

    async def deactivate(self, user_id, org):
        await self.repo.deactivate(user_id, org)
        await self.repo.db.commit()
        return {"status": "deactivated"}

    async def activate(self, user_id, org):
        await self.repo.activate(user_id, org)
        await self.repo.db.commit()
        return {"status": "activated"}