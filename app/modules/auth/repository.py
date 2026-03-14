from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AuthRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str):

        result = await self.db.execute(
            text("""
                SELECT
                    id,
                    email,
                    password_hash,
                    role,
                    organization_id
                FROM users
                WHERE email=:email
                AND active=true
            """),
            {"email": email},
        )

        return result.mappings().first()

    async def get_user_by_id(self, user_id: str):
        """
        Loads domain context for a verified Supabase identity.
        """
        result = await self.db.execute(
            text("""
                SELECT
                    id,
                    email,
                    role,
                    organization_id
                FROM users
                WHERE id=:id
                AND active=true
            """),
            {"id": user_id},
        )

        return result.mappings().first()

    async def bootstrap_user(self, user_id: str, email: str, full_name: str, role: str):
        """
        Structural Provisioning: Creates a new user record with organization_id = NULL.
        """
        r = await self.db.execute(
            text("""
                INSERT INTO users(id, email, full_name, role, organization_id, active)
                VALUES(:id, :email, :name, :role, NULL, true)
                RETURNING *
            """),
            {"id": user_id, "email": email, "name": full_name, "role": role}
        )
        await self.db.commit()
        return r.mappings().first()