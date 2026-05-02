from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_role

from .repository import TriageRepository
from .schemas import TriageCreate, TriageRead
from .service import TriageService

router = APIRouter(prefix="/triage", tags=["triage"])

def get_service(db: AsyncSession = Depends(get_db)):
    return TriageService(TriageRepository(db))

@router.post("", response_model=TriageRead)
async def create_triage(
    payload: TriageCreate,
    user=Depends(require_role("doctor", "nurse", "receptionist")),
    service: TriageService = Depends(get_service)
):
    """
    Registra los signos vitales (triage) de un paciente.
    Idealmente se llama después de cerrar una cita y antes de iniciar un encuentro.
    """
    return await service.create_triage(payload, user["org"], user["id"])

@router.get("/patient/{patient_id}", response_model=list[TriageRead])
async def get_patient_triage_history(
    patient_id: str,
    user=Depends(require_role("doctor", "nurse", "receptionist")),
    service: TriageService = Depends(get_service)
):
    """
    Obtiene el historial de triage de un paciente.
    """
    return await service.get_latest_by_patient(patient_id)

@router.get("/appointment/{appointment_id}", response_model=TriageRead)
async def get_triage_by_appointment(
    appointment_id: str,
    user=Depends(require_role("doctor", "nurse", "receptionist")),
    service: TriageService = Depends(get_service)
):
    """
    Obtiene el triage realizado para una cita específica.
    """
    triage = await service.get_by_appointment(appointment_id)
    if not triage:
        raise HTTPException(404, "Triage not found for this appointment")
    return triage

