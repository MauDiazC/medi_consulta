import logging
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from fastapi import HTTPException

from app.core.events import publish_event
from app.modules.organizations.repository import OrganizationRepository
from app.modules.patients.repository import PatientRepository
from app.modules.users.repository import UserRepository

from .models import Appointment, AppointmentNotification
from .notifier import AppointmentNotifier
from .repository import AppointmentRepository
from .schemas import SlotRead

logger = logging.getLogger("appointments.service")

# Global fallback store for OTPs in case Redis is not running (e.g., mock URL in tests)
_otp_fallback_store = {}


class AppointmentService:

    def __init__(self, repo: AppointmentRepository):
        self.repo = repo
        self.notifier = AppointmentNotifier()
        self.org_repo = OrganizationRepository(repo.db)
        self.user_repo = UserRepository(repo.db)

    def _format_mexico_phone(self, phone: str | None) -> str | None:
        if not phone:
            return None
        clean_phone = "".join(filter(str.isdigit, phone))
        if len(clean_phone) == 10:
            return f"52{clean_phone}"
        return clean_phone

    async def schedule(self, payload, org_id: str):
        # --- FETCH SETTINGS ---
        org = await self.org_repo.get(org_id)
        settings = org.get("settings", {}) if org else {}
        days_off = settings.get("days_off", {})

        # --- VALIDATIONS ---

        # 1. Ensure scheduled_at is UTC and normalized
        dt = payload.scheduled_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)

        # 2. Check Days Off
        weekday = dt.weekday()
        if weekday in days_off.get("weekdays", []):
            raise HTTPException(
                400, "La clínica no labora en este día de la semana"
            )

        specific_dates = days_off.get("specific_dates", [])
        if dt.strftime("%Y-%m-%d") in specific_dates:
            raise HTTPException(
                400, "La clínica no labora en esta fecha específica"
            )

        # 3. Check Business Hours (08:00 - 20:00)
        start_work = time(8, 0)
        end_work = time(20, 0)
        appt_time = dt.time()

        if appt_time < start_work or appt_time >= end_work:
            raise HTTPException(
                400, "Cita fuera del horario laboral (08:00 - 20:00)"
            )

        # 4. Check 40-minute slot alignment
        minutes_since_start = (dt.hour - 8) * 60 + dt.minute
        if minutes_since_start % 40 != 0:
            raise HTTPException(
                400,
                "La hora de la cita debe estar alinea a bloques de 40 minutos",
            )

        # 5. Check for double booking (Overlap)
        is_occupied = await self.repo.check_overlap(str(payload.doctor_id), dt)
        if is_occupied:
            raise HTTPException(
                409, "El horario seleccionado ya está ocupado por otra cita"
            )

        # --- PRE-PROCESSING ---
        if payload.metadata_json and "phone" in payload.metadata_json:
            payload.metadata_json["phone"] = self._format_mexico_phone(
                payload.metadata_json["phone"]
            )

        # --- EXECUTION ---
        appointment = Appointment(
            patient_id=payload.patient_id,
            organization_id=UUID(org_id),
            doctor_id=payload.doctor_id,
            scheduled_at=dt,
            metadata_json=payload.metadata_json or {},
        )
        saved = await self.repo.create(appointment)

        # Immediate welcome notification
        try:
            await self.create_and_send_notification(saved, "welcome")
        except Exception as e:
            logger.error(f"Error sending immediate notification: {str(e)}")

        return saved

    async def create_and_send_notification(
        self, appointment: Appointment, notification_type: str
    ) -> None:
        """Creates an AppointmentNotification record in 'pending' status, then

        attempts to send it via notifier. Updates status to 'sent' or 'failed'
        accordingly.
        """
        # 1. Create a pending notification record
        notification = AppointmentNotification(
            appointment_id=appointment.id,
            type=notification_type,
            status="pending",
        )
        self.repo.db.add(notification)
        await self.repo.db.commit()
        await self.repo.db.refresh(notification)

        # 2. Extract details
        details = await self.repo.get_full_details(str(appointment.id))
        if not details:
            notification.status = "failed"
            notification.error_message = "No details found for appointment"
            await self.repo.db.commit()
            return

        # Fetch Cascading WhatsApp credentials
        org_id = str(details["organization_id"])
        doctor_id = str(details["doctor_id"])

        # Try Doctor settings first
        doctor = await self.user_repo.get(doctor_id, org_id)
        doctor_settings = doctor.get("settings", {}) if doctor else {}
        whatsapp_config = doctor_settings.get("whatsapp", {})

        meta_token = whatsapp_config.get("token")
        phone_number_id = whatsapp_config.get("phone_number_id")

        # Fallback to Org settings
        if not meta_token or not phone_number_id:
            org = await self.org_repo.get(org_id)
            org_settings = org.get("settings", {}) if org else {}
            org_whatsapp = org_settings.get("whatsapp", {})
            meta_token = meta_token or org_whatsapp.get("token")
            phone_number_id = phone_number_id or org_whatsapp.get(
                "phone_number_id"
            )

        # Phone resolution
        phone = details.get("metadata_json", {}).get("phone")
        if not phone:
            patient_repo = PatientRepository(self.repo.db)
            patient = await patient_repo.get(str(details["patient_id"]), org_id)
            if patient:
                phone = patient.phone_number

        if not phone:
            notification.status = "failed"
            notification.error_message = "No phone number found"
            await self.repo.db.commit()
            logger.warning(
                f"No phone number found for appointment {appointment.id}"
            )
            return

        try:
            # Generate message
            ai_msg = await self.notifier.generate_ai_message(
                patient_name=details["patient_name"],
                doctor_name=details["doctor_name"],
                scheduled_at=details["scheduled_at"].strftime(
                    "%d/%m/%Y %H:%M"
                ),
                reason=details.get("metadata_json", {}).get(
                    "reason", "Consulta médica"
                ),
                reminder_type=notification_type,
            )

            # Send WhatsApp and get message ID
            wamid = await self.notifier.send_whatsapp(
                phone=phone,
                message=ai_msg,
                appointment_id=str(appointment.id),
                meta_token=meta_token,
                phone_number_id=phone_number_id,
            )

            if wamid:
                notification.status = "sent"
                notification.whatsapp_message_id = wamid
                notification.sent_at = datetime.now(UTC)
            else:
                notification.status = "failed"
                notification.error_message = (
                    "Meta API returned no message ID or failed"
                )

        except Exception as e:
            logger.error(
                f"Error sending notification {notification_type} for appointment {appointment.id}: {str(e)}"
            )
            notification.status = "failed"
            notification.error_message = str(e)

        await self.repo.db.commit()

    async def confirm(self, appointment_id: str, confirmed: bool):
        appointment = await self.repo.get_by_id(appointment_id)
        if not appointment:
            return None

        appointment.patient_confirmation = confirmed
        if confirmed:
            appointment.status = "confirmed"

        return await self.repo.update(appointment)

    async def update_status(self, appointment_id: str, status: str):
        appointment = await self.repo.get_by_id(appointment_id)
        if not appointment:
            return None

        appointment.status = status
        updated = await self.repo.update(appointment)

        # Publicar evento
        await publish_event(
            "appointment.updated",
            {
                "appointment_id": str(appointment.id),
                "status": appointment.status,
                "patient_id": str(appointment.patient_id),
            },
        )

        return updated

    async def cancel(self, appointment_id: str):
        appointment = await self.repo.get_by_id(appointment_id)
        if not appointment:
            return None

        appointment.status = "cancelled"
        updated = await self.repo.update(appointment)

        # Publicar evento
        await publish_event(
            "appointment.updated",
            {
                "appointment_id": str(appointment.id),
                "status": "cancelled",
                "patient_id": str(appointment.patient_id),
            },
        )

        return updated

    async def update_notification_status(
        self, wamid: str, status: str, error_message: str | None = None
    ) -> bool:
        """Updates status of an AppointmentNotification using its Meta message

        ID.
        """
        from sqlalchemy import select

        stmt = select(AppointmentNotification).where(
            AppointmentNotification.whatsapp_message_id == wamid
        )
        result = await self.repo.db.execute(stmt)
        notification = result.scalar_one_or_none()

        if not notification:
            logger.warning(
                f"No notification found for whatsapp_message_id: {wamid}"
            )
            return False

        notification.status = status
        if error_message:
            notification.error_message = error_message

        await self.repo.db.commit()
        return True

    async def get_notifications_for_appointment(self, appointment_id: str):
        """Lists all notifications for a specific appointment, sorted by

        creation date.
        """
        from sqlalchemy import select

        stmt = select(AppointmentNotification).where(
            AppointmentNotification.appointment_id == UUID(appointment_id)
        ).order_by(AppointmentNotification.created_at.asc())

        result = await self.repo.db.execute(stmt)
        return result.scalars().all()

    async def process_pending_reminders(self):
        """Logic for the background worker to scan and send pending reminders

        (12h, 3h, 15m).
        """
        from sqlalchemy import select, text

        now = datetime.now(UTC)

        # 1. 12h window: scheduled in the next 12 hours (but more than 3 hours away)
        twelve_h_upper = now + timedelta(hours=12)
        twelve_h_lower = now + timedelta(hours=3)

        stmt_12h = select(Appointment).where(
            Appointment.status == "scheduled",
            Appointment.scheduled_at > twelve_h_lower,
            Appointment.scheduled_at <= twelve_h_upper,
        )
        result = await self.repo.db.execute(stmt_12h)
        appointments_12h = result.scalars().all()

        for appt in appointments_12h:
            existing_stmt = text("""
                SELECT 1 FROM appointment_notifications
                WHERE appointment_id = :aid AND type = 'reminder_12h'
            """)
            has_notification = (
                await self.repo.db.execute(existing_stmt, {"aid": appt.id})
            ).scalar()
            if not has_notification:
                await self.create_and_send_notification(appt, "reminder_12h")

        # 2. 3h window: scheduled in the next 3 hours (but more than 15 minutes away)
        three_h_upper = now + timedelta(hours=3)
        three_h_lower = now + timedelta(minutes=15)

        stmt_3h = select(Appointment).where(
            Appointment.status == "scheduled",
            Appointment.scheduled_at > three_h_lower,
            Appointment.scheduled_at <= three_h_upper,
        )
        result = await self.repo.db.execute(stmt_3h)
        appointments_3h = result.scalars().all()

        for appt in appointments_3h:
            existing_stmt = text("""
                SELECT 1 FROM appointment_notifications
                WHERE appointment_id = :aid AND type = 'reminder_3h'
            """)
            has_notification = (
                await self.repo.db.execute(existing_stmt, {"aid": appt.id})
            ).scalar()
            if not has_notification:
                await self.create_and_send_notification(appt, "reminder_3h")

        # 3. 15m window: scheduled in the next 15 minutes (but in the future)
        fifteen_m_upper = now + timedelta(minutes=15)
        fifteen_m_lower = now

        stmt_15m = select(Appointment).where(
            Appointment.status == "scheduled",
            Appointment.scheduled_at > fifteen_m_lower,
            Appointment.scheduled_at <= fifteen_m_upper,
        )
        result = await self.repo.db.execute(stmt_15m)
        appointments_15m = result.scalars().all()

        for appt in appointments_15m:
            existing_stmt = text("""
                SELECT 1 FROM appointment_notifications
                WHERE appointment_id = :aid AND type = 'reminder_15m'
            """)
            has_notification = (
                await self.repo.db.execute(existing_stmt, {"aid": appt.id})
            ).scalar()
            if not has_notification:
                await self.create_and_send_notification(appt, "reminder_15m")

    async def process_whatsapp_reply(self, phone: str, message_text: str):
        """Incoming webhook processing."""
        # 1. Buscar paciente
        patient_repo = PatientRepository(self.repo.db)
        patient = await patient_repo.get_by_phone(phone)
        if not patient:
            logger.warning(f"WhatsApp reply from unknown phone: {phone}")
            return

        # 2. Buscar cita más reciente
        appointment = await self.repo.get_latest_for_patient(str(patient.id))
        if not appointment:
            logger.warning(
                f"WhatsApp reply from patient {patient.id} but no appointment found"
            )
            return

        # 3. Fetch Cascading WhatsApp credentials for response
        org_id = str(appointment.organization_id)
        doctor_id = str(appointment.doctor_id)

        # A. Try Doctor settings first
        doctor = await self.user_repo.get(doctor_id, org_id)
        doctor_settings = doctor.get("settings", {}) if doctor else {}
        whatsapp_config = doctor_settings.get("whatsapp", {})

        meta_token = whatsapp_config.get("token")
        phone_number_id = whatsapp_config.get("phone_number_id")

        # B. Fallback to Organization settings
        if not meta_token or not phone_number_id:
            org = await self.org_repo.get(org_id)
            org_settings = org.get("settings", {}) if org else {}
            org_whatsapp = org_settings.get("whatsapp", {})
            meta_token = meta_token or org_whatsapp.get("token")
            phone_number_id = phone_number_id or org_whatsapp.get(
                "phone_number_id"
            )

        # 4. Extraer intención
        intent = await self.notifier.extract_intent(message_text)

        reply_msg = (
            "He recibido tu mensaje. Un asistente humano lo revisará pronto."
        )
        if intent == "confirm":
            appointment.patient_confirmation = True
            appointment.status = "confirmed"
            await self.repo.update(appointment)
            reply_msg = "¡Gracias! Tu cita ha sido confirmada."
        elif intent == "cancel":
            appointment.patient_confirmation = False
            appointment.status = "cancelled"
            await self.repo.update(appointment)
            reply_msg = "Entendido. Tu cita ha sido cancelada. Si deseas reagendar, contáctanos."

        await self.notifier.send_whatsapp(
            phone=phone,
            message=reply_msg,
            appointment_id=str(appointment.id),
            meta_token=meta_token,
            phone_number_id=phone_number_id,
        )

        # Publicar evento para actualizar el dashboard en tiempo real
        await publish_event(
            "appointment.updated",
            {
                "appointment_id": str(appointment.id),
                "status": appointment.status,
                "patient_id": str(patient.id),
            },
        )

    async def list_by_org(
        self,
        org_id: str,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        patient_id: str | None = None,
        doctor_ids: list[str] | None = None,
    ):
        return await self.repo.list_by_org(
            org_id, status, start_date, end_date, patient_id, doctor_ids
        )

    async def get_availability(
        self, org_id: str, doctor_id: str, target_date: date
    ) -> list[SlotRead]:
        """Generates 40-minute slots from 08:00 to 20:00 and checks

        availability.
        """
        # Check Days Off
        org = await self.org_repo.get(org_id)
        settings = org.get("settings", {}) if org else {}
        days_off = settings.get("days_off", {})

        weekday = target_date.weekday()
        if weekday in days_off.get("weekdays", []):
            return []  # No slots on days off

        if target_date.strftime("%Y-%m-%d") in days_off.get(
            "specific_dates", []
        ):
            return []

        existing_appts = await self.repo.get_doctor_appointments_by_date(
            org_id, doctor_id, target_date
        )

        slots = []
        current_time = datetime.combine(target_date, time(8, 0)).replace(
            tzinfo=UTC
        )
        end_work_time = datetime.combine(target_date, time(20, 0)).replace(
            tzinfo=UTC
        )

        slot_duration = timedelta(minutes=40)

        while current_time + slot_duration <= end_work_time:
            slot_start = current_time
            slot_end = current_time + slot_duration

            # Check if any appointment overlaps with this slot
            occupied_by = None
            for appt in existing_appts:
                appt_time = appt.scheduled_at
                if appt_time.tzinfo is None:
                    appt_time = appt_time.replace(tzinfo=UTC)

                if slot_start <= appt_time < slot_end:
                    occupied_by = appt.id
                    break

            slots.append(
                SlotRead(
                    start_time=slot_start.strftime("%H:%M"),
                    end_time=slot_end.strftime("%H:%M"),
                    status="occupied" if occupied_by else "free",
                    appointment_id=occupied_by,
                )
            )

            current_time = slot_end

        return slots

    async def request_otp(self, payload) -> dict:
        """Generates a 4-digit OTP, stores it in Redis (or in-memory fallback),

        and sends it to the patient's phone number via WhatsApp.
        """
        import json
        import secrets

        from sqlalchemy import text

        from app.core.events import get_redis

        clean_phone = self._format_mexico_phone(payload.patient_phone)
        if not clean_phone:
            raise HTTPException(400, "Número de teléfono inválido")

        # 1. Fetch Doctor details (organization_id and full_name)
        stmt = text(
            "SELECT organization_id, full_name FROM users WHERE id = CAST(:doc_id AS UUID) LIMIT 1"
        )
        result = await self.repo.db.execute(stmt, {"doc_id": payload.doctor_id})
        doctor = result.mappings().first()
        if not doctor:
            raise HTTPException(404, "Médico no encontrado")

        org_id = str(doctor["organization_id"])
        doctor_name = doctor["full_name"]

        # 2. Fetch Cascading WhatsApp credentials
        doctor_user = await self.user_repo.get(str(payload.doctor_id), org_id)
        doctor_settings = doctor_user.get("settings", {}) if doctor_user else {}
        whatsapp_config = doctor_settings.get("whatsapp", {})

        meta_token = whatsapp_config.get("token")
        phone_number_id = whatsapp_config.get("phone_number_id")

        if not meta_token or not phone_number_id:
            org = await self.org_repo.get(org_id)
            org_settings = org.get("settings", {}) if org else {}
            org_whatsapp = org_settings.get("whatsapp", {})
            meta_token = meta_token or org_whatsapp.get("token")
            phone_number_id = phone_number_id or org_whatsapp.get(
                "phone_number_id"
            )

        # 3. Generate 4-digit OTP
        otp_code = f"{secrets.SystemRandom().randint(1000, 9999)}"

        # 4. Save to Redis / Fallback
        otp_payload = {
            "doctor_id": str(payload.doctor_id),
            "scheduled_at": payload.scheduled_at.isoformat(),
            "patient_name": payload.patient_name,
            "patient_email": payload.patient_email,
            "otp_code": otp_code,
            "metadata_json": payload.metadata_json or {},
        }

        r = get_redis()
        key = f"otp_appointment:{clean_phone}"
        value_data = json.dumps(otp_payload)

        if r is not None:
            await r.set(key, value_data, ex=600)  # 10 minutes expiration
        else:
            _otp_fallback_store[key] = (
                value_data,
                datetime.now(UTC) + timedelta(minutes=10),
            )

        # 5. Send OTP via WhatsApp
        otp_message = f"Hola {payload.patient_name}, tu código para confirmar tu cita con el Dr. {doctor_name} es: {otp_code}."

        await self.notifier.send_whatsapp(
            phone=clean_phone,
            message=otp_message,
            appointment_id="OTP_VERIFICATION",
            meta_token=meta_token,
            phone_number_id=phone_number_id,
        )

        return {"status": "otp_sent"}

    async def confirm_otp(self, payload) -> Appointment:
        """Validates the OTP code, resolves/creates the patient, schedules the

        appointment, and sends the welcome notification.
        """
        import json

        from sqlalchemy import text

        from app.core.events import get_redis
        from app.modules.patients.schemas import PatientCreate as PatientCreateSchema

        clean_phone = self._format_mexico_phone(payload.patient_phone)
        if not clean_phone:
            raise HTTPException(400, "Número de teléfono inválido")

        r = get_redis()
        key = f"otp_appointment:{clean_phone}"
        data = None

        if r is not None:
            data = await r.get(key)
        else:
            item = _otp_fallback_store.get(key)
            if item:
                val, expires_at = item
                if datetime.now(UTC) < expires_at:
                    data = val
                else:
                    _otp_fallback_store.pop(key, None)

        if not data:
            raise HTTPException(
                400, "El código OTP ha expirado o no existe en el sistema"
            )

        otp_data = json.loads(data)
        if otp_data["otp_code"] != payload.otp_code.strip():
            raise HTTPException(400, "Código de verificación incorrecto")

        doctor_id = otp_data["doctor_id"]
        scheduled_at = datetime.fromisoformat(otp_data["scheduled_at"])
        patient_name = otp_data["patient_name"]
        patient_email = otp_data["patient_email"]
        metadata_json = otp_data["metadata_json"]

        # 1. Fetch Doctor organization
        stmt = text(
            "SELECT organization_id FROM users WHERE id = CAST(:doc_id AS UUID) LIMIT 1"
        )
        result = await self.repo.db.execute(stmt, {"doc_id": doctor_id})
        doctor = result.mappings().first()
        if not doctor:
            raise HTTPException(404, "Médico no encontrado")

        org_id = str(doctor["organization_id"])

        # 2. Lookup or Create Patient under org_id
        patient_repo = PatientRepository(self.repo.db)

        ten_digits = (
            clean_phone[-10:] if len(clean_phone) >= 10 else clean_phone
        )
        with_52 = f"52{ten_digits}"

        r_patient = await self.repo.db.execute(
            text("""
            SELECT * FROM patients
            WHERE organization_id = CAST(:org_id AS UUID)
              AND (phone_number = :p1 OR phone_number = :p2 OR phone_number = :p3)
            LIMIT 1
        """),
            {"org_id": org_id, "p1": ten_digits, "p2": with_52, "p3": f"+{with_52}"},
        )
        patient = r_patient.mappings().first()

        if not patient:
            names = patient_name.strip().split(" ", 1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else ""

            new_patient_payload = PatientCreateSchema(
                first_name=first_name,
                last_name=last_name,
                phone_number=clean_phone,
                email=patient_email,
            )
            patient = await patient_repo.create(new_patient_payload, org_id)

        # 3. Create the appointment payload and schedule it
        from .schemas import AppointmentCreate as AppointmentCreateSchema

        appt_create_payload = AppointmentCreateSchema(
            patient_id=UUID(str(patient["id"])),
            doctor_id=UUID(doctor_id),
            scheduled_at=scheduled_at,
            metadata_json={**metadata_json, "phone": clean_phone},
        )

        appointment = await self.schedule(appt_create_payload, org_id)

        # 4. Clean up OTP data
        if r is not None:
            await r.delete(key)
        else:
            _otp_fallback_store.pop(key, None)

        return appointment
