from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ProfessionalIdentityRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, user_id, org_id, public_key_pem, license_number, specialty=None):
        """Creates or updates the professional identity of a physician."""
        # UPSERT logic using PostgreSQL syntax
        await self.db.execute(
            text("""
                INSERT INTO professional_identities (
                    user_id, organization_id, public_key_pem, license_number, specialty
                )
                VALUES (
                    CAST(:uid AS UUID), CAST(:oid AS UUID), :key, :license, :spec
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    public_key_pem = EXCLUDED.public_key_pem,
                    license_number = EXCLUDED.license_number,
                    specialty = EXCLUDED.specialty,
                    is_active = true,
                    updated_at = NOW()
            """),
            {
                "uid": user_id,
                "oid": org_id,
                "key": public_key_pem,
                "license": license_number,
                "spec": specialty
            }
        )
        await self.db.commit()

    async def get_by_user(self, user_id: str, org_id: str):
        """Fetch identity validating organization."""
        r = await self.db.execute(
            text("""
                SELECT * FROM professional_identities 
                WHERE user_id = CAST(:uid AS UUID) 
                AND organization_id = CAST(:oid AS UUID)
            """),
            {"uid": user_id, "oid": org_id}
        )
        return r.mappings().first()

    async def deactivate(self, user_id: str, org_id: str):
        """Disables the professional identity."""
        await self.db.execute(
            text("""
                UPDATE professional_identities 
                SET is_active = false, updated_at = NOW()
                WHERE user_id = CAST(:uid AS UUID) AND organization_id = CAST(:oid AS UUID)
            """),
            {"uid": user_id, "oid": org_id}
        )
        await self.db.commit()

    async def activate(self, user_id: str, org_id: str):
        """Re-enables the professional identity."""
        await self.db.execute(
            text("""
                UPDATE professional_identities 
                SET is_active = true, updated_at = NOW()
                WHERE user_id = CAST(:uid AS UUID) AND organization_id = CAST(:oid AS UUID)
            """),
            {"uid": user_id, "oid": org_id}
        )
        await self.db.commit()
