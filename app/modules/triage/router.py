from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from .schemas import TriageCreate, TriageRead
from .repository import TriageRepository
from .service import TriageService

router = APIRouter(prefix="/triage", tags=["triage"])

def get_service(db: AsyncSession = Depends(get_db)):
    return TriageService(TriageRepository(db))

@router.post("", response_model=TriageRead)
async def create_triage(
    payload: TriageCreate,
    user=Depends(get_current_user),
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
    user=Depends(get_current_user),
    service: TriageService = Depends(get_service)
):
    """
    Obtiene el historial de triage de un paciente.
    """
    return await service.get_latest_by_patient(patient_id)
