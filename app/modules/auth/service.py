import secrets
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.core.security import (create_access_token, verify_password, hash_password)
from app.core.email import EmailService
from app.core.config import settings
from .repository import AuthRepository
from google.oauth2 import id_token
from google.auth.transport import requests

class AuthService:

    def __init__(self, repo: AuthRepository):
        self.repo = repo

    async def register_saas(self, org_name: str, email: str, password: str, full_name: str):
        """Atomic Onboarding: Creates organization and admin user in one transaction."""
        existing = await self.repo.get_user_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists",
            )

        # 1. Create Organization
        org = await self.repo.create_organization(org_name)
        
        # 2. Create Admin User linked to that Org
        password_hash = hash_password(password)
        user = await self.repo.create_user(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            role="admin",
            organization_id=org["id"]
        )
        
        # 3. Commit Atomic transaction
        await self.repo.commit()

        # 4. Issue Token and Metadata
        token = create_access_token({
            "sub": str(user["id"]),
            "email": user["email"],
            "org": str(user["organization_id"]),
            "role": user["role"],
        })
        
        return {
            "access_token": token,
            "user_id": str(user["id"]),
            "organization_id": str(user["organization_id"]),
            "role": user["role"],
            "email": user["email"],
            "full_name": user["full_name"]
        }

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
        return {
            "access_token": token,
            "user_id": str(user["id"]),
            "organization_id": org_id,
            "role": user["role"],
            "email": user["email"],
            "full_name": user["full_name"]
        }

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

        # Logic for Task 1: If assistant, try to get doctor's name
        full_name = user["full_name"]
        if user["role"] == "assistant" and org_id:
            doc_name = await self.repo.get_doctor_name_by_org(org_id)
            if doc_name:
                full_name = doc_name

        token = create_access_token(
            {
                "sub": str(user["id"]),
                "email": user["email"],
                "org": org_id,
                "role": user["role"],
            }
        )

        return {
            "access_token": token,
            "user_id": str(user["id"]),
            "organization_id": org_id,
            "role": user["role"],
            "email": user["email"],
            "full_name": full_name
        }

    async def google_login(self, credential: str, client_info: dict = None):
        """
        Verifies Google ID Token and manages user lifecycle.
        Bridges Google Identity with Institutional Authorization.
        """
        try:
            # 1. Verify Google Identity
            idinfo = id_token.verify_oauth2_token(
                credential, requests.Request(), settings.GOOGLE_CLIENT_ID
            )

            # 2. Extract Identity Claims
            email = idinfo['email']
            full_name_google = idinfo.get('name', 'Google User')
            
            # 3. Resolve Domain Identity
            user = await self.repo.get_user_by_email(email)

            if not user:
                # 4. Auto-provisioning (First login via Google)
                # Password hash is NULL for social users (cannot login via password unless reset)
                user = await self.repo.create_user(
                    email=email,
                    full_name=full_name_google,
                    password_hash=None, 
                    role="doctor"
                )
                await self.repo.commit()
            
            # 5. Notify and issue Institutional Token
            await EmailService.send_login_notification(
                self.repo.db, 
                email, 
                client_info or {"method": "google", "timestamp": datetime.now(timezone.utc).isoformat()}
            )
            await self.repo.commit()

            org_id = str(user["organization_id"]) if user["organization_id"] else None
            
            # Logic for Task 1: If assistant, try to get doctor's name
            full_name = user["full_name"]
            if user["role"] == "assistant" and org_id:
                doc_name = await self.repo.get_doctor_name_by_org(org_id)
                if doc_name:
                    full_name = doc_name

            token = create_access_token({
                "sub": str(user["id"]),
                "email": user["email"],
                "org": org_id,
                "role": user["role"],
            })

            return {
                "access_token": token,
                "user_id": str(user["id"]),
                "organization_id": org_id,
                "role": user["role"],
                "email": user["email"],
                "full_name": full_name
            }

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Google authentication failed: {str(e)}"
            )

    async def forgot_password(self, email: str):
        """Generates a secure reset token and sends it via email."""
        user = await self.repo.get_user_by_email(email)
        
        if user:
            token = secrets.token_urlsafe(32)
            await self.repo.create_reset_token(str(user["id"]), token)
            await EmailService.send_password_reset(self.repo.db, email, token)
            await self.repo.commit()
        
        return True 

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
