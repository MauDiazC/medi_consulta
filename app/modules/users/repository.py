from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, email, password_hash, full_name, role, org):
        r = await self.db.execute(
            text("""
                INSERT INTO users(
                    email,password_hash,full_name,role,
                    organization_id,active
                )
                VALUES(:e,:p,:f,:r,CAST(:o AS UUID),true)
                RETURNING *
            """),
            {"e": email, "p": password_hash, "f": full_name, "r": role, "o": org},
        )
        # Commit removed for service-level atomicity
        return r.mappings().first()

    async def list(self, org, limit, offset):
        r = await self.db.execute(
            text("""
                SELECT *
                FROM users
                WHERE organization_id=CAST(:org AS UUID)
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"org": org, "limit": limit, "offset": offset},
        )
        return r.mappings().all()

    async def get(self, user_id, org):
        r = await self.db.execute(
            text("""
                SELECT *
                FROM users
                WHERE id=CAST(:id AS UUID) AND organization_id=CAST(:org AS UUID)
            """),
            {"id": user_id, "org": org},
        )
        return r.mappings().first()

    async def update(self, user_id, org, payload):
        r = await self.db.execute(
            text("""
                UPDATE users
                SET role = COALESCE(:role, role)
                WHERE id=CAST(:id AS UUID) AND organization_id=CAST(:org AS UUID)
                RETURNING *
            """),
            {"id": user_id, "org": org, "role": payload.role},
        )
        # Commit removed for service-level atomicity
        return r.mappings().first()

    async def deactivate(self, user_id, org):
        await self.db.execute(
            text("""
                UPDATE users
                SET active=false
                WHERE id=CAST(:id AS UUID) AND organization_id=CAST(:org AS UUID)
            """),
            {"id": user_id, "org": org},
        )
        # Commit removed for service-level atomicity

    async def activate(self, user_id, org):
        """Re-enables a user account."""
        await self.db.execute(
            text("""
                UPDATE users
                SET active=true
                WHERE id=CAST(:id AS UUID) AND organization_id=CAST(:org AS UUID)
            """),
            {"id": user_id, "org": org},
        )
        # Commit removed for service-level atomicity

    async def assign_organization(self, user_id: str, organization_id: str):
        """
        Authoritative method for bootstrap onboarding linkage.
        """
        await self.db.execute(
            text("UPDATE users SET organization_id = CAST(:org_id AS UUID) WHERE id = CAST(:user_id AS UUID)"),
            {"org_id": organization_id, "user_id": user_id}
        )

    async def get_by_email(self, email: str):
        """Fetch user by email for authentication or bootstrap checks."""
        r = await self.db.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {"email": email.lower().strip()}
        )
        return r.mappings().first()

    async def hard_delete_by_email(self, email: str):
        """DANGER: Physical deletion of user. Use only for dev/testing."""
        await self.db.execute(
            text("DELETE FROM users WHERE email = :email"),
            {"email": email.lower().strip()}
        )
        await self.db.commit()
