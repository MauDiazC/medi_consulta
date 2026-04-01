from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from .schemas import AppointmentCreate, AppointmentRead, AppointmentUpdate
from .service import AppointmentService
from .repository import AppointmentRepository

router = APIRouter(prefix="/appointments", tags=["appointments"])

def get_service(db: AsyncSession = Depends(get_db)):
    return AppointmentService(AppointmentRepository(db))

@router.post("/", response_model=AppointmentRead)
async def schedule_appointment(
    payload: AppointmentCreate,
    user=Depends(get_current_user),
    service: AppointmentService = Depends(get_service)
):
    return await service.schedule(payload, user["org"])

@router.patch("/{appointment_id}/confirm", response_model=AppointmentRead)
async def confirm_appointment(
    appointment_id: str,
    payload: AppointmentUpdate,
    service: AppointmentService = Depends(get_service)
):
    # This can be called by n8n without a user token if we implement specific security
    # For now, we assume it's an authorized internal call
    if payload.patient_confirmation is None:
        raise HTTPException(400, "patient_confirmation is required")
    
    updated = await service.confirm(appointment_id, payload.patient_confirmation)
    if not updated:
        raise HTTPException(404, "Appointment not found")
    return updated

@router.get("/", response_model=list[AppointmentRead])
async def list_appointments(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = AppointmentRepository(db)
    return await repo.list_by_org(user["org"])
