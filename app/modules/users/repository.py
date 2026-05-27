import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, email, password_hash, full_name, role, org, slug=None):
        r = await self.db.execute(
            text("""
                INSERT INTO users(
                    email,password_hash,full_name,role,
                    organization_id,active,slug
                )
                VALUES(:e,:p,:f,:r,CAST(:o AS UUID),true,:slug)
                RETURNING *
            """),
            {
                "e": email,
                "p": password_hash,
                "f": full_name,
                "r": role,
                "o": org,
                "slug": slug,
            },
        )
        # Commit removed for service-level atomicity
        return r.mappings().first()

    async def list_all(self, org, limit, offset):
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
        settings_json = (
            json.dumps(payload.settings) if payload.settings is not None else None
        )
        r = await self.db.execute(
            text("""
                UPDATE users
                SET role = COALESCE(:role, role),
                    full_name = COALESCE(:full_name, full_name),
                    settings = COALESCE(CAST(:settings AS JSONB), settings),
                    slug = COALESCE(:slug, slug)
                WHERE id=CAST(:id AS UUID) AND organization_id=CAST(:org AS UUID)
                RETURNING *
            """),
            {
                "id": user_id,
                "org": org,
                "role": payload.role,
                "full_name": payload.full_name,
                "settings": settings_json,
                "slug": payload.slug,
            },
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
            text(
                "UPDATE users SET organization_id = CAST(:org_id AS UUID) WHERE id = CAST(:user_id AS UUID)"
            ),
            {"org_id": organization_id, "user_id": user_id},
        )

    async def get_by_email(self, email: str):
        """Fetch user by email for authentication or bootstrap checks."""
        r = await self.db.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {"email": email.lower().strip()},
        )
        return r.mappings().first()

    async def hard_delete_by_email(self, email: str):
        """DANGER: Physical deletion of user. Use only for dev/testing."""
        await self.db.execute(
            text("DELETE FROM users WHERE email = :email"),
            {"email": email.lower().strip()},
        )
        await self.db.commit()

    # --- Staff Assignments ---

    async def assign_doctor(self, staff_id: str, doctor_id: str):
        await self.db.execute(
            text("""
                INSERT INTO staff_assignments(staff_id, doctor_id)
                VALUES(CAST(:sid AS UUID), CAST(:did AS UUID))
                ON CONFLICT DO NOTHING
            """),
            {"sid": staff_id, "did": doctor_id},
        )
        await self.db.commit()

    async def remove_assignment(self, staff_id: str, doctor_id: str):
        await self.db.execute(
            text("""
                DELETE FROM staff_assignments
                WHERE staff_id=CAST(:sid AS UUID) AND doctor_id=CAST(:did AS UUID)
            """),
            {"sid": staff_id, "did": doctor_id},
        )
        await self.db.commit()

    async def get_assigned_doctors(self, staff_id: str) -> list[str]:
        result = await self.db.execute(
            text("""
                SELECT doctor_id
                FROM staff_assignments
                WHERE staff_id=CAST(:sid AS UUID)
            """),
            {"sid": staff_id},
        )
        return [str(row[0]) for row in result.all()]

    async def generate_unique_slug(self, full_name: str, exclude_user_id: str | None = None) -> str:
        import re
        import unicodedata

        base_slug = full_name.lower().strip()
        base_slug = unicodedata.normalize('NFKD', base_slug).encode('ascii', 'ignore').decode('utf-8')
        base_slug = re.sub(r'[^a-z0-9]+', '-', base_slug)
        base_slug = re.sub(r'-+', '-', base_slug).strip('-')
        if not base_slug:
            base_slug = "doctor"

        slug = base_slug
        counter = 1
        while True:
            if exclude_user_id:
                stmt = text("SELECT id FROM users WHERE slug = :slug AND id != CAST(:exclude_id AS UUID) LIMIT 1")
                params = {"slug": slug, "exclude_id": exclude_user_id}
            else:
                stmt = text("SELECT id FROM users WHERE slug = :slug LIMIT 1")
                params = {"slug": slug}

            result = await self.db.execute(stmt, params)
            if not result.first():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug
