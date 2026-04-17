from fastapi import APIRouter, Depends, status, Request
from app.core.database import get_db
from .repository import AuthRepository
from .schemas import (
    LoginRequest, TokenResponse, RegisterRequest, 
    ForgotPasswordRequest, ResetPasswordRequest, 
    GoogleLoginRequest, SaaSRegistrationRequest
)
from .service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

def get_service(db=Depends(get_db)):
    return AuthService(AuthRepository(db))

@router.post("/register-saas", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_saas(payload: SaaSRegistrationRequest, s=Depends(get_service)):
    """
    Self-Service Onboarding.
    Creates an organization and its first admin user in one atomic step.
    """
    return await s.register_saas(
        org_name=payload.organization_name,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name
    )

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, s=Depends(get_service)):
    """Institutional Registration Flow."""
    return await s.register(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role
    )

@router.post("/login", response_model=TokenResponse)
async def login(request: Request, payload: LoginRequest, s=Depends(get_service)):
    """Institutional Login Flow with notification."""
    client_info = {
        "user_agent": request.headers.get("user-agent"),
        "host": request.client.host,
    }
    return await s.login(payload.email, payload.password, client_info=client_info)

@router.post("/google", response_model=TokenResponse)
async def google_login(request: Request, payload: GoogleLoginRequest, s=Depends(get_service)):
    """Institutional Google Social Auth."""
    client_info = {
        "user_agent": request.headers.get("user-agent"),
        "host": request.client.host,
        "method": "google"
    }
    return await s.google_login(payload.credential, client_info=client_info)

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, s=Depends(get_service)):
    """Institutional Reset Request."""
    await s.forgot_password(payload.email)
    return {"message": "Si el correo existe, se ha enviado un enlace de recuperación."}

@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, s=Depends(get_service)):
    """Institutional Reset Execution."""
    await s.reset_password(payload.token, payload.new_password)
    return {"message": "Contraseña actualizada exitosamente."}
