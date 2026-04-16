import logging
from typing import Any
from app.core.events import publish_event_tx
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("core.email")

class EmailService:
    """
    Institutional Email Service.
    Uses the Transactional Outbox pattern for high-integrity delivery.
    """
    
    @staticmethod
    async def send_login_notification(db: AsyncSession, email: str, metadata: dict[str, Any]):
        """Notifies user of a new successful login."""
        await publish_event_tx(db, "auth.login_notification", {
            "to": email,
            "subject": "Nuevo inicio de sesión detectado",
            "metadata": metadata
        })
        logger.info(f"Login notification event published for {email}")

    @staticmethod
    async def send_password_reset(db: AsyncSession, email: str, reset_token: str):
        """Sends a password reset link/token to the user."""
        await publish_event_tx(db, "auth.password_reset", {
            "to": email,
            "subject": "Recuperación de contraseña",
            "token": reset_token
        })
        logger.info(f"Password reset event published for {email}")
