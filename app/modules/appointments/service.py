import logging
from datetime import datetime, timezone, date, timedelta, time
from uuid import UUID
from .models import Appointment
from .repository import AppointmentRepository
from .notifier import AppointmentNotifier
from .schemas import SlotRead
from app.modules.patients.repository import PatientRepository
from app.core.events import publish_event

logger = logging.getLogger("appointments.service")

class AppointmentService:
    def __init__(self, repo: AppointmentRepository):
        self.repo = repo
        self.notifier = AppointmentNotifier()

    async def schedule(self, payload, org_id: str):
        appointment = Appointment(
            patient_id=payload.patient_id,
            organization_id=UUID(org_id),
            doctor_id=payload.doctor_id,
            scheduled_at=payload.scheduled_at,
            metadata_json=payload.metadata_json or {}
        )
        saved = await self.repo.create(appointment)
        
        # Immediate notification
        await self.trigger_notification(str(saved.id), "immediate")
        saved.reminder_immediate_sent = True
        await self.repo.update(saved)
        
        return saved

    async def trigger_notification(self, appointment_id: str, reminder_type: str):
        details = await self.repo.get_full_details(appointment_id)
        if not details: return

        # Get phone from metadata or fallback
        phone = details.get("metadata_json", {}).get("phone")
        if not phone:
            # Fallback to patient profile if phone is not in metadata
            patient_repo = PatientRepository(self.repo.db)
            patient = await patient_repo.get(str(details["patient_id"]), str(details["organization_id"]))
            if patient:
                phone = patient.phone_number

        if not phone:
            logger.warning(f"No phone number found for appointment {appointment_id}")
            return

        ai_msg = await self.notifier.generate_ai_message(
            patient_name=details["patient_name"],
            doctor_name=details["doctor_name"],
            scheduled_at=details["scheduled_at"].strftime("%d/%m/%Y %H:%M"),
            reason=details.get("metadata_json", {}).get("reason", "Consulta médica"),
            reminder_type=reminder_type
        )

        await self.notifier.send_whatsapp(phone, ai_msg, appointment_id)

    async def confirm(self, appointment_id: str, confirmed: bool):
        appointment = await self.repo.get_by_id(appointment_id)
        if not appointment: return None
        
        appointment.patient_confirmation = confirmed
        if confirmed:
            appointment.status = "confirmed"
        
        return await self.repo.update(appointment)

    async def update_status(self, appointment_id: str, status: str):
        appointment = await self.repo.get_by_id(appointment_id)
        if not appointment: return None
        
        appointment.status = status
        updated = await self.repo.update(appointment)
        
        # Publicar evento para actualizar el dashboard
        await publish_event("appointment.updated", {
            "appointment_id": str(appointment.id),
            "status": appointment.status,
            "patient_id": str(appointment.patient_id)
        })
        
        return updated

    async def process_pending_reminders(self):
        """
        Logic for the background worker.
        """
        # 12h window (poll appointments in next 12 hours)
        twelve_h = await self.repo.get_pending_reminders(720, "reminder_12h_sent")
        for appt in twelve_h:
            await self.trigger_notification(str(appt.id), "12h")
            appt.reminder_12h_sent = True
            await self.repo.update(appt)

        # 5m window
        five_m = await self.repo.get_pending_reminders(5, "reminder_5m_sent")
        for appt in five_m:
            await self.trigger_notification(str(appt.id), "5m")
            appt.reminder_5m_sent = True
            await self.repo.update(appt)

    async def process_whatsapp_reply(self, phone: str, message_text: str):
        """
        Incoming webhook processing.
        """
        # 1. Buscar paciente
        patient_repo = PatientRepository(self.repo.db)
        patient = await patient_repo.get_by_phone(phone)
        if not patient:
            logger.warning(f"WhatsApp reply from unknown phone: {phone}")
            return

        # 2. Buscar cita más reciente
        appointment = await self.repo.get_latest_for_patient(str(patient.id))
        if not appointment:
            logger.warning(f"WhatsApp reply from patient {patient.id} but no appointment found")
            return

        # 3. Extraer intención
        intent = await self.notifier.extract_intent(message_text)
        
        if intent == "confirm":
            appointment.patient_confirmation = True
            appointment.status = "confirmed"
            await self.repo.update(appointment)
            await self.notifier.send_whatsapp(phone, "¡Gracias! Tu cita ha sido confirmada.", str(appointment.id))
        elif intent == "cancel":
            appointment.patient_confirmation = False
            appointment.status = "cancelled"
            await self.repo.update(appointment)
            await self.notifier.send_whatsapp(phone, "Entendido. Tu cita ha sido cancelada. Si deseas reagendar, contáctanos.", str(appointment.id))
        else:
            # Quizás es una duda, podrías notificar al doctor o responder algo genérico
            await self.notifier.send_whatsapp(phone, "He recibido tu mensaje. Un asistente humano lo revisará pronto.", str(appointment.id))
        
        # Publicar evento para actualizar el dashboard en tiempo real
        await publish_event("appointment.updated", {
            "appointment_id": str(appointment.id),
            "status": appointment.status,
            "patient_id": str(patient.id)
        })

    async def list_by_org(
        self, 
        org_id: str, 
        status: str | None = None, 
        start_date: datetime | None = None, 
        end_date: datetime | None = None,
        patient_id: str | None = None
    ):
        return await self.repo.list_by_org(org_id, status, start_date, end_date, patient_id)

    async def get_availability(self, org_id: str, doctor_id: str, target_date: date) -> list[SlotRead]:
        """
        Generates 40-minute slots from 08:00 to 20:00 and checks availability.
        """
        existing_appts = await self.repo.get_doctor_appointments_by_date(org_id, doctor_id, target_date)
        
        slots = []
        current_time = datetime.combine(target_date, time(8, 0)).replace(tzinfo=timezone.utc)
        end_work_time = datetime.combine(target_date, time(20, 0)).replace(tzinfo=timezone.utc)
        
        slot_duration = timedelta(minutes=40)
        
        while current_time + slot_duration <= end_work_time:
            slot_start = current_time
            slot_end = current_time + slot_duration
            
            # Check if any appointment overlaps with this slot
            # For simplicity, we check if an appointment starts within the slot
            occupied_by = None
            for appt in existing_appts:
                if slot_start <= appt.scheduled_at < slot_end:
                    occupied_by = appt.id
                    break
            
            slots.append(SlotRead(
                start_time=slot_start.strftime("%H:%M"),
                end_time=slot_end.strftime("%H:%M"),
                status="occupied" if occupied_by else "free",
                appointment_id=occupied_by
            ))
            
            current_time = slot_end
            
        return slots
