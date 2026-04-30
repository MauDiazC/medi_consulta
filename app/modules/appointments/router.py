import logging
from datetime import datetime, timezone, time, date as date_type
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_authorized_doctor_ids
from app.core.permissions import require_role
from app.core.config import settings
from .schemas import AppointmentCreate, AppointmentRead, AppointmentUpdate, SlotRead
from .service import AppointmentService
from .repository import AppointmentRepository

logger = logging.getLogger("appointments.router")

router = APIRouter(prefix="/appointments", tags=["appointments"])

def get_service(db: AsyncSession = Depends(get_db)):
    return AppointmentService(AppointmentRepository(db))

@router.post("", response_model=AppointmentRead)
async def schedule_appointment(
    payload: AppointmentCreate,
    user=Depends(require_role("doctor", "nurse", "receptionist", "assistant")),
    authorized_doctor_ids=Depends(get_authorized_doctor_ids),
    service: AppointmentService = Depends(get_service)
):
    # Security: Ensure the user is authorized to schedule for this doctor
    if str(payload.doctor_id) not in authorized_doctor_ids:
        raise HTTPException(403, "Not authorized to schedule appointments for this doctor")
        
    return await service.schedule(payload, user["org"])

@router.patch("/{appointment_id}/confirm", response_model=AppointmentRead)
async def confirm_appointment(
    appointment_id: str,
    payload: AppointmentUpdate,
    service: AppointmentService = Depends(get_service)
):
    if payload.patient_confirmation is None:
        raise HTTPException(400, "patient_confirmation is required")
    
    updated = await service.confirm(appointment_id, payload.patient_confirmation)
    if not updated:
        raise HTTPException(404, "Appointment not found")
    return updated

@router.patch("/{appointment_id}/attend", response_model=AppointmentRead)
async def attend_appointment(
    appointment_id: str,
    user=Depends(require_role("doctor", "nurse", "receptionist", "assistant")),
    service: AppointmentService = Depends(get_service)
):
    """
    Marca la cita como atendida (cerrada). 
    Este es el paso previo a la toma de signos (triage).
    """
    updated = await service.update_status(appointment_id, "attended")
    if not updated:
        raise HTTPException(404, "Appointment not found")
    return updated

@router.get("", response_model=list[AppointmentRead])
async def list_appointments(
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    patient_id: Optional[str] = None,
    user=Depends(require_role("doctor", "nurse", "receptionist", "assistant", "admin")),
    authorized_doctor_ids=Depends(get_authorized_doctor_ids),
    service: AppointmentService = Depends(get_service)
):
    """
    Lista las citas de la organización. Filtra por doctores autorizados.
    """
    # Si no hay fechas y NO se está filtrando por paciente, definimos el rango de "hoy"
    if not start_date and not end_date and not patient_id:
        today = datetime.now(timezone.utc).date()
        start_date = datetime.combine(today, time.min).replace(tzinfo=timezone.utc)
        end_date = datetime.combine(today, time.max).replace(tzinfo=timezone.utc)
    
    return await service.list_by_org(user["org"], status, start_date, end_date, patient_id, authorized_doctor_ids)


@router.get("/patient/{patient_id}", response_model=list[AppointmentRead])
async def list_appointments_by_patient(
    patient_id: str,
    user=Depends(require_role("doctor", "nurse", "receptionist", "assistant", "admin")),
    authorized_doctor_ids=Depends(get_authorized_doctor_ids),
    service: AppointmentService = Depends(get_service)
):
    """
    Obtiene todo el historial de citas de un paciente específico, filtrado por doctores autorizados.
    """
    return await service.list_by_org(user["org"], patient_id=patient_id, doctor_ids=authorized_doctor_ids)

@router.get("/availability", response_model=list[SlotRead])
async def get_availability(
    doctor_id: str,
    target_date: Optional[date_type] = None,
    user=Depends(require_role("doctor", "nurse", "receptionist", "assistant", "admin")),
    authorized_doctor_ids=Depends(get_authorized_doctor_ids),
    service: AppointmentService = Depends(get_service)
):
    """
    Returns 40-minute availability slots for a specific doctor on a given date.
    """
    if doctor_id not in authorized_doctor_ids:
        raise HTTPException(403, "Not authorized to view availability for this doctor")

    if not target_date:
        target_date = datetime.now(timezone.utc).date()
        
    return await service.get_availability(user["org"], doctor_id, target_date)

# --- Meta Cloud API Webhooks ---

@router.get("/webhook")
async def verify_webhook(request: Request):
    """
    Verification endpoint for Meta Webhooks.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    if mode == "subscribe" and token == settings.get("META_VERIFY_TOKEN"):
        logger.info("Meta Webhook verified successfully")
        return Response(content=challenge)
    
    logger.warning("Meta Webhook verification failed: Invalid token")
    raise HTTPException(403, "Invalid verify token")

@router.post("/webhook")
async def receive_webhook(request: Request, service: AppointmentService = Depends(get_service)):
    """
    Receives incoming WhatsApp messages from patients.
    """
    try:
        payload = await request.json()
        
        # Meta payload structure is nested
        entries = payload.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    from_phone = msg.get("from")
                    msg_text = msg.get("text", {}).get("body")
                    
                    if from_phone and msg_text:
                        logger.info(f"WhatsApp message received from {from_phone}: {msg_text[:50]}...")
                        # En una app de alta carga, esto debería ir a una cola de ARQ
                        await service.process_whatsapp_reply(from_phone, msg_text)
                        
    except Exception as e:
        logger.error(f"Error processing Meta webhook: {str(e)}")
        # Siempre retornamos 200 a Meta para evitar reintentos infinitos si el error es de lógica
        
    return {"status": "ok"}
