from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SaaSRegistrationRequest(BaseModel):
    """Schema for self-service SaaS onboarding."""
    organization_name: str
    email: EmailStr
    password: str
    full_name: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "doctor"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class GoogleLoginRequest(BaseModel):
    credential: str # The ID Token from Google Frontend

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    organization_id: Optional[str] = None
    role: str
    email: str
    full_name: str


class TokenExchangeRequest(BaseModel):
    access_token: str
