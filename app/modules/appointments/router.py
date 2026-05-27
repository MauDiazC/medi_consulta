import logging
from datetime import date as date_type
from datetime import datetime, time

import pytz
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_authorized_doctor_ids
from app.core.permissions import require_role

from .repository import AppointmentRepository
from .schemas import (
    AppointmentCreate,
    AppointmentNotificationRead,
    AppointmentRead,
    AppointmentUpdate,
    OTPConfirmPayload,
    OTPRequestPayload,
    SlotRead,
)
from .service import AppointmentService

logger = logging.getLogger("appointments.router")

router = APIRouter(prefix="/appointments", tags=["appointments"])


def get_service(db: AsyncSession = Depends(get_db)):
    return AppointmentService(AppointmentRepository(db))


@router.post("", response_model=AppointmentRead)
async def schedule_appointment(
    payload: AppointmentCreate,
    user=Depends(require_role("doctor", "nurse", "receptionist", "assistant")),
    authorized_doctor_ids=Depends(get_authorized_doctor_ids),
    service: AppointmentService = Depends(get_service),
):
    # Security: Ensure the user is authorized to schedule for this doctor
    if str(payload.doctor_id) not in authorized_doctor_ids:
        raise HTTPException(
            403, "Not authorized to schedule appointments for this doctor"
        )

    return await service.schedule(payload, user["org"])


@router.patch("/{appointment_id}/confirm", response_model=AppointmentRead)
async def confirm_appointment(
    appointment_id: str,
    payload: AppointmentUpdate,
    service: AppointmentService = Depends(get_service),
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
    service: AppointmentService = Depends(get_service),
):
    """Marca la cita como atendida (cerrada).

    Este es el paso previo a la toma de signos (triage).
    """
    updated = await service.update_status(appointment_id, "attended")
    if not updated:
        raise HTTPException(404, "Appointment not found")
    return updated


@router.patch("/{appointment_id}/cancel", response_model=AppointmentRead)
async def cancel_appointment(
    appointment_id: str,
    user=Depends(require_role("doctor", "nurse", "receptionist", "assistant")),
    service: AppointmentService = Depends(get_service),
):
    """Cancela la cita y libera el slot de tiempo."""
    updated = await service.cancel(appointment_id)
    if not updated:
        raise HTTPException(404, "Appointment not found")
    return updated


@router.get("", response_model=list[AppointmentRead])
async def list_appointments(
    status: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    patient_id: str | None = None,
    doctor_id: str | None = None,
    user=Depends(require_role("doctor", "nurse", "receptionist", "assistant", "admin")),
    service: AppointmentService = Depends(get_service),
):
    """Lista las citas de la organización. Filtra por doctores y aplica control de accesos.

    Usa la zona horaria de CDMX por defecto para el filtro de 'hoy'.
    """
    org_id = user["org"]
    role = user["role"]

    # Control de acceso y visibilidad
    if role == "doctor":
        # Los doctores solo ven sus propias citas
        filter_doctor_ids = [user["sub"]]
    elif doctor_id:
        # Los asistentes/admins pueden filtrar por un médico específico
        filter_doctor_ids = [doctor_id]
    else:
        # Calendario general de la clínica para asistentes/admins
        filter_doctor_ids = None

    # Si no hay fechas y NO se está filtrando por paciente, definimos el rango de "hoy" en CDMX
    if not start_date and not end_date and not patient_id:
        tz = pytz.timezone("America/Mexico_City")
        today_local = datetime.now(tz).date()

        # Convertimos el inicio y fin del día local a UTC para la consulta en DB
        local_start = datetime.combine(today_local, time.min)
        local_end = datetime.combine(today_local, time.max)

        # Localizar y convertir a UTC
        start_date = tz.localize(local_start).astimezone(pytz.UTC)
        end_date = tz.localize(local_end).astimezone(pytz.UTC)

    return await service.list_by_org(
        org_id=org_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        patient_id=patient_id,
        doctor_ids=filter_doctor_ids,
    )


@router.get("/patient/{patient_id}", response_model=list[AppointmentRead])
async def list_appointments_by_patient(
    patient_id: str,
    user=Depends(require_role("doctor", "nurse", "receptionist", "assistant", "admin")),
    authorized_doctor_ids=Depends(get_authorized_doctor_ids),
    service: AppointmentService = Depends(get_service),
):
    """Obtiene todo el historial de citas de un paciente específico, filtrado

    por doctores autorizados.
    """
    return await service.list_by_org(
        user["org"], patient_id=patient_id, doctor_ids=authorized_doctor_ids
    )


@router.get("/availability", response_model=list[SlotRead])
async def get_availability(
    doctor_id: str,
    target_date: date_type | None = None,
    user=Depends(require_role("doctor", "nurse", "receptionist", "assistant", "admin")),
    authorized_doctor_ids=Depends(get_authorized_doctor_ids),
    service: AppointmentService = Depends(get_service),
):
    """Returns 40-minute availability slots for a specific doctor on a given

    date.
    """
    if doctor_id not in authorized_doctor_ids:
        raise HTTPException(403, "Not authorized to view availability for this doctor")

    if not target_date:
        tz = pytz.timezone("America/Mexico_City")
        target_date = datetime.now(tz).date()

    return await service.get_availability(user["org"], doctor_id, target_date)


# --- Meta Cloud API Webhooks ---


@router.get("/webhook")
async def verify_webhook(request: Request):
    """Verification endpoint for Meta Webhooks."""
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
async def receive_webhook(
    request: Request, service: AppointmentService = Depends(get_service)
):
    """Receives incoming WhatsApp messages and status callbacks from

    patients/Meta.
    """
    try:
        payload = await request.json()

        # Meta payload structure is nested
        entries = payload.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})

                # A. Handle status updates (delivered, read, failed, etc.)
                statuses = value.get("statuses", [])
                for status in statuses:
                    wamid = status.get("id")
                    status_str = status.get("status")
                    error_msg = None
                    if status_str == "failed":
                        errors = status.get("errors", [])
                        if errors:
                            error_msg = errors[0].get("title", "Unknown error")
                    if wamid and status_str:
                        logger.info(f"WhatsApp status update for {wamid}: {status_str}")
                        await service.update_notification_status(
                            wamid, status_str, error_msg
                        )

                # B. Handle incoming replies (confirm, cancel, etc.)
                messages = value.get("messages", [])
                for msg in messages:
                    from_phone = msg.get("from")
                    msg_text = msg.get("text", {}).get("body")

                    if from_phone and msg_text:
                        logger.info(
                            f"WhatsApp message received from {from_phone}: {msg_text[:50]}..."
                        )
                        await service.process_whatsapp_reply(from_phone, msg_text)

    except Exception as e:
        logger.error(f"Error processing Meta webhook: {str(e)}")
        # Siempre retornamos 200 a Meta para evitar reintentos infinitos si el error es de lógica

    return {"status": "ok"}


@router.get(
    "/{appointment_id}/notifications",
    response_model=list[AppointmentNotificationRead],
)
async def get_appointment_notifications(
    appointment_id: str,
    user=Depends(require_role("doctor", "nurse", "receptionist", "assistant", "admin")),
    service: AppointmentService = Depends(get_service),
):
    """Returns the message delivery history/timeline for a specific

    appointment.
    """
    appointment = await service.repo.get_by_id(appointment_id)
    if not appointment or str(appointment.organization_id) != user["org"]:
        raise HTTPException(404, "Appointment not found")

    return await service.get_notifications_for_appointment(appointment_id)


@router.get("/public/doctor/{doctor_id_or_slug}/availability", response_model=list[SlotRead])
async def get_public_availability(
    doctor_id_or_slug: str,
    target_date: date_type | None = None,
    service: AppointmentService = Depends(get_service),
):
    """Obtiene la disponibilidad de bloques de un médico de forma pública usando su ID o slug."""
    from uuid import UUID

    from sqlalchemy import text

    is_uuid = False
    try:
        UUID(doctor_id_or_slug)
        is_uuid = True
    except ValueError:
        pass

    if is_uuid:
        stmt = text("SELECT id, organization_id FROM users WHERE id = CAST(:val AS UUID) LIMIT 1")
    else:
        stmt = text("SELECT id, organization_id FROM users WHERE slug = :val LIMIT 1")

    result = await service.repo.db.execute(stmt, {"val": doctor_id_or_slug})
    doctor = result.mappings().first()
    if not doctor:
        raise HTTPException(404, "Médico no encontrado")

    doctor_id = str(doctor["id"])
    org_id = str(doctor["organization_id"])
    if not target_date:
        tz = pytz.timezone("America/Mexico_City")
        target_date = datetime.now(tz).date()

    return await service.get_availability(org_id, doctor_id, target_date)


@router.post("/public/request-otp")
async def request_otp(
    payload: OTPRequestPayload,
    service: AppointmentService = Depends(get_service),
):
    """Solicita la generación del código OTP y su envío por WhatsApp."""
    return await service.request_otp(payload)


@router.post("/public/confirm-otp", response_model=AppointmentRead)
async def confirm_otp(
    payload: OTPConfirmPayload,
    service: AppointmentService = Depends(get_service),
):
    """Recibe el código OTP del paciente, valida e inserta la cita en la base de datos."""
    return await service.confirm_otp(payload)

