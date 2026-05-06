from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ClinicalSessionRepository:

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(
        self,
        name: str,
        organization_id: str,
        user_id: str,
    ):
        result = await self._db.execute(
            text("""
                INSERT INTO clinical_sessions (
                    name,
                    organization_id,
                    user_id,
                    is_active
                )
                VALUES (
                    :name,
                    CAST(:organization_id AS UUID),
                    CAST(:user_id AS UUID),
                    true
                )
                RETURNING *
            """),
            {
                "name": name,
                "organization_id": organization_id,
                "user_id": user_id,
            },
        )

        await self._db.commit()
        return result.mappings().first()

    async def list(
        self, 
        org_id: str, 
        limit: int = 10, 
        offset: int = 0, 
        is_active: bool = None,
        authorized_doctor_ids: list[str] = None
    ):
        """List sessions for an organization with optional status and doctor filters."""
        query = "SELECT * FROM clinical_sessions WHERE organization_id = CAST(:org_id AS UUID)"
        params = {"org_id": org_id, "limit": limit, "offset": offset}
        
        if is_active is not None:
            query += " AND is_active = :is_active"
            params["is_active"] = is_active
            
        if authorized_doctor_ids is not None:
            if not authorized_doctor_ids:
                return []
            query += " AND user_id = ANY(:doctor_ids)"
            params["doctor_ids"] = authorized_doctor_ids
            
        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        
        r = await self._db.execute(text(query), params)
        return r.mappings().all()

    async def get(self, session_id: str, org_id: str, authorized_doctor_ids: list[str] = None):
        """Get a specific session validating organization and doctor authorization."""
        query = "SELECT * FROM clinical_sessions WHERE id = CAST(:id AS UUID) AND organization_id = CAST(:org_id AS UUID)"
        params = {"id": session_id, "org_id": org_id}
        
        if authorized_doctor_ids is not None:
            if not authorized_doctor_ids:
                return None
            query += " AND user_id = ANY(:doctor_ids)"
            params["doctor_ids"] = authorized_doctor_ids
            
        r = await self._db.execute(text(query), params)
        return r.mappings().first()

    async def get_encounters(self, session_id: str, org_id: str):
        """
        Lists all encounters in a session. 
        Note: Access to the session itself should be validated before calling this.
        """
        r = await self._db.execute(
            text("""
                SELECT e.*, 
                       p.first_name || ' ' || p.last_name as patient_name,
                       u.full_name as doctor_name
                FROM encounters e
                JOIN patients p ON e.patient_id = p.id
                JOIN users u ON e.doctor_id = u.id
                WHERE e.clinical_session_id = CAST(:sid AS UUID)
                  AND e.organization_id = CAST(:org_id AS UUID)
                ORDER BY e.created_at ASC
            """),
            {"sid": session_id, "org_id": org_id}
        )
        return r.mappings().all()

    async def deactivate(self, session_id: str, org_id: str):
        """Close/deactivate a clinical session."""
        await self._db.execute(
            text("""
                UPDATE clinical_sessions
                SET is_active = false,
                    closed_at = now()
                WHERE id = CAST(:id AS UUID) AND organization_id = CAST(:org_id AS UUID)
            """),
            {"id": session_id, "org_id": org_id}
        )
        await self._db.commit()

    async def close(self, session_id: str, org_id: str):
        """Semantic alias for closing a clinical session with timestamp."""
        return await self.deactivate(session_id, org_id)

    async def activate(self, session_id: str, org_id: str):
        """Re-open/activate a clinical session."""
        await self._db.execute(
            text("""
                UPDATE clinical_sessions
                SET is_active = true,
                    closed_at = NULL
                WHERE id = CAST(:id AS UUID) AND organization_id = CAST(:org_id AS UUID)
            """),
            {"id": session_id, "org_id": org_id}
        )
        await self._db.commit()
