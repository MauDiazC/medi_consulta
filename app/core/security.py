from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

# Professional Hashing Context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours shift

def hash_password(password: str) -> str:
    """Institutional Grade Hashing."""
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies password against stored hash."""
    return pwd_context.verify(password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Signs a local JWT with the institutional SECRET_KEY.
    No external dependencies (Supabase) required.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token: str) -> dict:
    """
    Local forensic verification of identity.
    Decodes JWT using internal secret.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise ValueError("Could not validate credentials")

def normalize_identity(payload: dict) -> dict:
    """Standardizes identity claims for the clinical system."""
    return {
        "id": str(payload.get("sub")),
        "email": str(payload.get("email")).lower().strip(),
        "organization_id": payload.get("organization_id")
    }
