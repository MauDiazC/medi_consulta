import asyncio
import logging
from datetime import datetime, timezone
from app.core.database import AsyncSessionLocal
from app.modules.appointments.service import AppointmentService
from app.modules.appointments.repository import AppointmentRepository
from app.core.worker_settings import get_redis_settings

# Configuración de Logging específica para Citas
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker.appointments")

async def run_appointment_scheduler():
    """
    Loop dedicado para el escaneo de citas próximas (12h, 5m).
    Se ejecuta de forma independiente para evitar interferencias con el Outbox.
    """
    logger.info("Appointment Scheduler Loop started")
    while True:
        try:
            async with AsyncSessionLocal() as db:
                service = AppointmentService(AppointmentRepository(db))
                await service.process_pending_reminders()
        except Exception as e:
            logger.error(f"Appointment scheduler error: {str(e)}", exc_info=True)
        
        # Escaneo cada 30 segundos para mayor precisión en recordatorios de 5m
        await asyncio.sleep(30)

class AppointmentWorkerSettings:
    """
    Configuración para el worker de ARQ (si necesitamos encolar tareas de citas).
    """
    functions = [] # Aquí irían tareas pesadas específicas de citas si las hubiera
    redis_settings = get_redis_settings()
    
    @staticmethod
    async def on_startup(ctx):
        logger.info("Appointments Dedicated Worker starting...")
        ctx['scheduler_task'] = asyncio.create_task(run_appointment_scheduler())

    @staticmethod
    async def on_shutdown(ctx):
        logger.info("Appointments Dedicated Worker shutting down...")
        if 'scheduler_task' in ctx:
            ctx['scheduler_task'].cancel()

if __name__ == "__main__":
    print("Use 'arq app.worker.appointments_worker.AppointmentWorkerSettings' to run this worker.")
    asyncio.run(run_appointment_scheduler())
