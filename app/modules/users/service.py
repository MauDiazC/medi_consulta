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
                detail=f"El correo {payload.email} ya está registrado.",
            )

        slug = None
        if payload.role == "doctor":
            slug = await self.repo.generate_unique_slug(payload.full_name)

        user = await self.repo.create(
            payload.email,
            hash_password(payload.password),
            payload.full_name,
            payload.role,
            payload.organization_id,
            slug=slug,
        )

        # 2. Persist to DB
        await self.repo.db.commit()
        return user

    async def list_all(self, org, limit, offset):
        return await self.repo.list_all(org, limit, offset)

    async def get(self, user_id, org):
        user = await self.repo.get(user_id, org)
        if not user:
            raise HTTPException(404, "User not found")
        return user

    async def update(self, user_id, org, payload):
        from sqlalchemy import text
        current_user = await self.repo.get(user_id, org)
        if not current_user:
            raise HTTPException(404, "User not found")

        if payload.slug is not None:
            import re
            cleaned_slug = payload.slug.lower().strip()
            cleaned_slug = re.sub(r'[^a-z0-9]+', '-', cleaned_slug).strip('-')
            if not cleaned_slug:
                raise HTTPException(400, "El slug no puede estar vacío o contener solo caracteres especiales")

            stmt = text("SELECT id FROM users WHERE slug = :slug AND id != CAST(:exclude_id AS UUID) LIMIT 1")
            chk = await self.repo.db.execute(stmt, {"slug": cleaned_slug, "exclude_id": user_id})
            if chk.first():
                raise HTTPException(400, f"El enlace público '{cleaned_slug}' ya está en uso por otro médico.")
            payload.slug = cleaned_slug
        elif payload.full_name is not None and current_user.get("role") == "doctor" and not current_user.get("slug"):
            payload.slug = await self.repo.generate_unique_slug(payload.full_name, exclude_user_id=user_id)

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

    # --- Staff Assignments ---

    async def assign_doctor(self, staff_id: str, doctor_id: str, org_id: str):
        # Verify both users exist in the same organization
        staff = await self.repo.get(staff_id, org_id)
        doctor = await self.repo.get(doctor_id, org_id)

        if not staff or not doctor:
            raise HTTPException(404, "Staff or Doctor not found in this organization")

        if doctor["role"] != "doctor":
            raise HTTPException(400, "The target user for assignment must be a doctor")

        await self.repo.assign_doctor(staff_id, doctor_id)
        return {"status": "assigned"}

    async def remove_assignment(self, staff_id: str, doctor_id: str, org_id: str):
        await self.repo.remove_assignment(staff_id, doctor_id)
        return {"status": "removed"}

    async def get_assigned_doctors(self, staff_id: str, org_id: str):
        # Verify staff exists
        await self.get(staff_id, org_id)
        return await self.repo.get_assigned_doctors(staff_id)
