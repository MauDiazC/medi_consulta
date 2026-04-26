from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Triage

class TriageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, triage: Triage) -> Triage:
        self.db.add(triage)
        await self.db.commit()
        await self.db.refresh(triage)
        return triage

    async def get_by_appointment(self, appointment_id: str) -> Triage | None:
        result = await self.db.execute(
            select(Triage).where(Triage.appointment_id == appointment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_patient(self, patient_id: str, limit: int = 5):
        result = await self.db.execute(
            select(Triage)
            .where(Triage.patient_id == patient_id)
            .order_by(Triage.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
