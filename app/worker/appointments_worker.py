import logging
from arq import cron
from app.core.database import AsyncSessionLocal
from app.modules.appointments.service import AppointmentService
from app.modules.appointments.repository import AppointmentRepository
from app.core.worker_settings import get_redis_settings

# Configuración de Logging específica para Citas
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker.appointments")

async def run_appointment_check(ctx):
    """
    Tarea programada que escanea citas próximas (12h, 5m).
    Ejecutada por el motor de cron de arq.
    """
    logger.info("Running scheduled appointment check...")
    try:
        async with AsyncSessionLocal() as db:
            service = AppointmentService(AppointmentRepository(db))
            await service.process_pending_reminders()
    except Exception as e:
        logger.error(f"Error in appointment check task: {str(e)}", exc_info=True)

class AppointmentWorkerSettings:
    """
    Configuración para el worker de ARQ dedicado a citas.
    """
    # Registramos una función dummy y el cron job para satisfacer a arq
    functions = [] 
    
    # Ejecutar cada 30 segundos (segundo 0 y segundo 30 de cada minuto)
    cron_jobs = [
        cron(run_appointment_check, second={0, 30})
    ]
    
    redis_settings = get_redis_settings()
    
    @staticmethod
    async def on_startup(ctx):
        logger.info("Appointments Dedicated Worker starting with arq cron...")

    @staticmethod
    async def on_shutdown(ctx):
        logger.info("Appointments Dedicated Worker shutting down...")

if __name__ == "__main__":
    print("Use 'arq app.worker.appointments_worker.AppointmentWorkerSettings' to run this worker.")
