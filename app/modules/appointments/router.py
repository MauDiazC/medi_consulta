import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import settings
from .schemas import AppointmentCreate, AppointmentRead, AppointmentUpdate
from .service import AppointmentService
from .repository import AppointmentRepository

logger = logging.getLogger("appointments.router")

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
    if payload.patient_confirmation is None:
        raise HTTPException(400, "patient_confirmation is required")
    
    updated = await service.confirm(appointment_id, payload.patient_confirmation)
    if not updated:
        raise HTTPException(404, "Appointment not found")
    return updated

@router.patch("/{appointment_id}/attend", response_model=AppointmentRead)
async def attend_appointment(
    appointment_id: str,
    user=Depends(get_current_user),
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

@router.get("/", response_model=list[AppointmentRead])
async def list_appointments(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = AppointmentRepository(db)
    return await repo.list_by_org(user["org"])

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
