import secrets
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.core.security import (create_access_token, verify_password, hash_password)
from app.core.email import EmailService
from .repository import AuthRepository

class AuthService:

    def __init__(self, repo: AuthRepository):
        self.repo = repo

    async def register(self, email: str, password: str, full_name: str, role: str):
        """Institutional Registration with Argon2."""
        existing = await self.repo.get_user_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists",
            )
        
        password_hash = hash_password(password)
        user = await self.repo.create_user(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            role=role
        )
        await self.repo.commit()

        org_id = str(user["organization_id"]) if user["organization_id"] else None
        
        token = create_access_token(
            {
                "sub": str(user["id"]),
                "email": user["email"],
                "org": org_id,
                "role": user["role"],
            }
        )
        return token

    async def login(self, email: str, password: str, client_info: dict = None):
        """Institutional Login with local Argon2 verification and Email Notification."""
        user = await self.repo.get_user_by_email(email)

        if not user or not user["password_hash"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not verify_password(
            password,
            user["password_hash"],
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        # Institutional login notification
        await EmailService.send_login_notification(
            self.repo.db, 
            email, 
            client_info or {"timestamp": datetime.now(timezone.utc).isoformat()}
        )
        await self.repo.commit()

        # Preserve null if organization_id is missing (Bootstrap case)
        org_id = str(user["organization_id"]) if user["organization_id"] else None

        token = create_access_token(
            {
                "sub": str(user["id"]),
                "email": user["email"],
                "org": org_id,
                "role": user["role"],
            }
        )

        return token

    async def forgot_password(self, email: str):
        """Generates a secure reset token and sends it via email."""
        user = await self.repo.get_user_by_email(email)
        
        # Security Note: We don't reveal if the user exists for privacy, 
        # but in this internal medical system we might prioritize usability.
        if user:
            token = secrets.token_urlsafe(32)
            await self.repo.create_reset_token(str(user["id"]), token)
            await EmailService.send_password_reset(self.repo.db, email, token)
            await self.repo.commit()
        
        return True # Always return success to prevent user enumeration

    async def reset_password(self, token: str, new_password: str):
        """Verifies reset token and updates password."""
        record = await self.repo.get_reset_token(token)
        
        if not record:
            raise HTTPException(status_code=400, detail="Token inválido")
        
        if record["used_at"]:
            raise HTTPException(status_code=400, detail="Token ya utilizado")
            
        if record["expires_at"] < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Token expirado")

        new_hash = hash_password(new_password)
        await self.repo.update_password(str(record["user_id"]), new_hash, token)
        return True
