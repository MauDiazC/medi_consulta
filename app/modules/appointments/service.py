from datetime import datetime, timezone
from uuid import UUID
from .models import Appointment
from .repository import AppointmentRepository
from .notifier import AppointmentNotifier
from app.core.events import publish_event

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
            # In a real scenario, we'd fetch it from Patient profile
            # For now, we expect it in metadata for the n8n integration
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
        appointment = await self.repo.get(appointment_id)
        if not appointment: return None
        
        appointment.patient_confirmation = confirmed
        if confirmed:
            appointment.status = "confirmed"
        
        return await self.repo.update(appointment)

    async def process_pending_reminders(self):
        """
        Logic for the background worker.
        """
        # 8h window (poll appointments in next 8 hours)
        eight_h = await self.repo.get_pending_reminders(480, "reminder_8h_sent")
        for appt in eight_h:
            await self.trigger_notification(str(appt.id), "8h")
            appt.reminder_8h_sent = True
            await self.repo.update(appt)

        # 15m window
        fifteen_m = await self.repo.get_pending_reminders(15, "reminder_15m_sent")
        for appt in fifteen_m:
            await self.trigger_notification(str(appt.id), "15m")
            appt.reminder_15m_sent = True
            await self.repo.update(appt)
