from datetime import datetime, timedelta, timezone
import time
import httpx
import logging
from typing import Any
from jose import jwt, jwk
from passlib.context import CryptContext
from app.core.config import settings

SECRET_KEY = "CHANGE_ME_LATER"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWKS Cache for Supabase Public Keys
_jwks_cache = {"keys": None, "expiry": 0}
JWKS_TTL = 600  # 10 minutes

async def get_supabase_jwks():
    """
    Retrieves and caches Supabase public keys for RS256/ES256 verification.
    """
    global _jwks_cache
    now = time.time()
    if _jwks_cache["keys"] and now < _jwks_cache["expiry"]:
        return _jwks_cache["keys"]

    # Normalization: Ensure clean base URL for OIDC discovery
    supabase_url = settings.SUPABASE_URL.strip().rstrip("/")
    url = f"{supabase_url}/auth/v1/.well-known/jwks.json"

    async with httpx.AsyncClient() as client:
        # Standard OIDC discovery endpoint - Do NOT send apikey header
        resp = await client.get(url)
        resp.raise_for_status()
        _jwks_cache = {"keys": resp.json(), "expiry": now + JWKS_TTL}
        return _jwks_cache["keys"]

async def verify_supabase_token(token: str) -> dict:
    """
    Forensic verification of Supabase Identity.
    Enforces ES256 algorithm and strict issuer/audience validation.
    """
    jwks = await get_supabase_jwks()
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    # 1. Select correct key from project JWKS
    key_data = next((k for k in jwks["keys"] if k["kid"] == kid), None)
    if not key_data:
        raise ValueError("Invalid key ID (kid). Identity origin cannot be verified.")

    public_key = jwk.construct(key_data)

    # 2. Institutional Anchors derived from normalized URL
    supabase_url = settings.SUPABASE_URL.strip().rstrip("/")
    expected_iss = f"{supabase_url}/auth/v1"

    # 3. Cryptographic & Claim Validation
    return jwt.decode(
        token, 
        public_key.to_pem().decode("utf-8"), 
        algorithms=["ES256"],
        audience="authenticated",
        issuer=expected_iss
    )

def normalize_supabase_identity(claims: dict) -> dict:
    """
    Institutional Normalization Layer for Supabase OIDC.
    Standardizes claims and applies sanitization safeguards.
    """
    sub = claims.get("sub")
    email = claims.get("email")

    if not sub or not email:
        raise ValueError("Identity verification failed: missing sub or email claims")

    # Fallback chain: metadata.full_name -> email -> "User"
    metadata = claims.get("user_metadata", {})
    raw_name = metadata.get("full_name") or email or "User"

    # Sanitization Safeguards
    # 1. Truncate to institutional maximum (120 chars)
    # 2. Trim whitespace
    # 3. Normalize email casing
    normalized_name = str(raw_name).strip()[:120]
    normalized_email = str(email).lower().strip()

    return {
        "id": str(sub),
        "email": normalized_email,
        "full_name": normalized_name
    }

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: dict[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = subject | {"exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)