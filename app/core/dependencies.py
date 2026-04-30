from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import ALGORITHM
from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger("core.dependencies")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)) -> dict:
    """
    Robust extraction of local identity.
    Handles manual header check if standard scheme fails.
    """
    if not token:
        # Fallback: manually check header (sometimes auto_error fails with middlewares)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        logger.warning("Authentication attempt without token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"JWT Decode Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

async def get_authorized_doctor_ids(
    user=Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
) -> list[str]:
    """
    Returns a list of doctor IDs the current user is authorized to view.
    - Doctors only see themselves.
    - Other roles (assistant, nurse, admin) see only assigned doctors.
    """
    role = user.get("role")
    user_id = user.get("sub")
    
    if role == "doctor":
        return [user_id]
        
    # For all other roles, check staff_assignments
    result = await db.execute(
        text("""
            SELECT doctor_id
            FROM staff_assignments
            WHERE staff_id=CAST(:sid AS UUID)
        """),
        {"sid": user_id}
    )
    return [str(row[0]) for row in result.all()]
