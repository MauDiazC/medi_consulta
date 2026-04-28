from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from .models import Appointment

class AppointmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, appointment: Appointment):
        self.db.add(appointment)
        await self.db.commit()
        await self.db.refresh(appointment)
        return appointment

    async def get(self, appointment_id: str):
        return await self.db.get(Appointment, appointment_id)

    async def list_by_org(
        self, 
        org_id: str, 
        status: str | None = None, 
        start_date: datetime | None = None, 
        end_date: datetime | None = None,
        patient_id: str | None = None
    ):
        stmt = select(Appointment).where(Appointment.organization_id == org_id)
        
        if status:
            stmt = stmt.where(Appointment.status == status)
        
        if start_date:
            stmt = stmt.where(Appointment.scheduled_at >= start_date)
            
        if end_date:
            stmt = stmt.where(Appointment.scheduled_at <= end_date)
            
        if patient_id:
            stmt = stmt.where(Appointment.patient_id == patient_id)

        stmt = stmt.order_by(Appointment.scheduled_at.asc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update(self, appointment: Appointment):
        await self.db.commit()
        await self.db.refresh(appointment)
        return appointment

    async def get_pending_reminders(self, window_minutes: int, reminder_field: str):
        """
        Poll appointments that are within the target window and haven't sent the specified reminder.
        """
        now = datetime.now(timezone.utc)
        target_time = now + timedelta(minutes=window_minutes)
        
        # We look for appointments scheduled in the next 'window_minutes'
        # reminder_field can be 'reminder_8h_sent' or 'reminder_15m_sent'
        stmt = select(Appointment).where(
            and_(
                Appointment.status == "scheduled",
                getattr(Appointment, reminder_field) == False,
                Appointment.scheduled_at <= target_time,
                Appointment.scheduled_at > now
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_latest_for_patient(self, patient_id: str):
        """
        Busca la cita más reciente (ya sea futura o pasada cercana) para un paciente.
        """
        stmt = select(Appointment).where(
            Appointment.patient_id == patient_id
        ).order_by(Appointment.scheduled_at.desc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_full_details(self, appointment_id: str):
        """
        Joins with patients and doctors to get names for the AI.
        """
        stmt = text("""
            SELECT 
                a.*, 
                p.first_name as patient_name,
                u.full_name as doctor_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN users u ON a.doctor_id = u.id
            WHERE a.id = :aid
        """)
        result = await self.db.execute(stmt, {"aid": appointment_id})
        return result.mappings().first()
