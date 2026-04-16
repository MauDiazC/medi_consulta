from datetime import datetime, timezone, timedelta
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

    async def create_user(self, email: str, full_name: str, password_hash: str, role: str):
        """
        Institutional Provisioning for new users.
        """
        r = await self.db.execute(
            text("""
                INSERT INTO users(email, full_name, password_hash, role, organization_id, active)
                VALUES(:email, :name, :hash, :role, NULL, true)
                RETURNING id, email, role, organization_id
            """),
            {"email": email, "name": full_name, "hash": password_hash, "role": role}
        )
        return r.mappings().first()

    async def create_reset_token(self, user_id: str, token: str, expires_in_minutes: int = 60):
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        await self.db.execute(
            text("""
                INSERT INTO password_reset_tokens(user_id, token, expires_at)
                VALUES(:uid, :token, :exp)
            """),
            {"uid": user_id, "token": token, "exp": expires_at}
        )

    async def get_reset_token(self, token: str):
        result = await self.db.execute(
            text("""
                SELECT user_id, expires_at, used_at
                FROM password_reset_tokens
                WHERE token=:token
            """),
            {"token": token}
        )
        return result.mappings().first()

    async def update_password(self, user_id: str, password_hash: str, token: str):
        # Update password
        await self.db.execute(
            text("UPDATE users SET password_hash=:hash WHERE id=:uid"),
            {"hash": password_hash, "uid": user_id}
        )
        # Mark token as used
        await self.db.execute(
            text("UPDATE password_reset_tokens SET used_at=now() WHERE token=:token"),
            {"token": token}
        )
        await self.db.commit()

    async def commit(self):
        await self.db.commit()
