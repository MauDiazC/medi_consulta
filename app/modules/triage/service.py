from .models import Triage
from .repository import TriageRepository
from .schemas import TriageCreate

class TriageService:
    def __init__(self, repository: TriageRepository):
        self.repository = repository

    async def create_triage(self, payload: TriageCreate, organization_id: str, doctor_id: str) -> Triage:
        triage = Triage(
            patient_id=payload.patient_id,
            appointment_id=payload.appointment_id,
            organization_id=organization_id,
            doctor_id=doctor_id,
            heart_rate=payload.heart_rate,
            oxygen_saturation=payload.oxygen_saturation,
            blood_pressure=payload.blood_pressure,
            weight=payload.weight,
            height=payload.height,
            temperature=payload.temperature
        )
        return await self.repository.create(triage)

    async def get_latest_by_patient(self, patient_id: str):
        return await self.repository.get_by_patient(patient_id)
