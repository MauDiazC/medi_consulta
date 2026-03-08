from fastapi import APIRouter, Depends, status

from app.core.database import get_db

from .repository import AuthRepository
from .schemas import LoginRequest, TokenResponse, TokenExchangeRequest
from .service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_service(db=Depends(get_db)):
    return AuthService(AuthRepository(db))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, s=Depends(get_service)):
    token = await s.login(payload.email, payload.password)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/exchange", response_model=TokenResponse)
async def exchange_token(payload: TokenExchangeRequest, s=Depends(get_service)):
    """
    Hardened Token Exchange Endpoint.
    Bridges Supabase JWTs into Mediconsulta authorization.
    """
    token = await s.exchange(payload.access_token)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/bootstrap", response_model=TokenResponse)
async def bootstrap_token(payload: TokenExchangeRequest, s=Depends(get_service)):
    """
    Hardened Genesis Onboarding Endpoint.
    Provisions new domain identities from verified external OIDC providers.
    """
    token = await s.bootstrap(payload.access_token)
    return {"access_token": token, "token_type": "bearer"}
