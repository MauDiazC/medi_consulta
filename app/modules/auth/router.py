from fastapi import APIRouter, Depends, status, Request
from app.core.database import get_db
from .repository import AuthRepository
from .schemas import LoginRequest, TokenResponse, RegisterRequest, ForgotPasswordRequest, ResetPasswordRequest
from .service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

def get_service(db=Depends(get_db)):
    return AuthService(AuthRepository(db))

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, s=Depends(get_service)):
    """Institutional Registration Flow."""
    token = await s.register(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role
    )
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=TokenResponse)
async def login(request: Request, payload: LoginRequest, s=Depends(get_service)):
    """Institutional Login Flow with notification."""
    client_info = {
        "user_agent": request.headers.get("user-agent"),
        "host": request.client.host,
    }
    token = await s.login(payload.email, payload.password, client_info=client_info)
    return {"access_token": token, "token_type": "bearer"}

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
