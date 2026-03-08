from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user

from .repository import ClinicalSessionRepository
from .schemas import ClinicalSessionCreate
from .service import ClinicalSessionService

router = APIRouter(
    prefix="/clinical-sessions",
    tags=["clinical_sessions"],
)


def get_service(db: AsyncSession = Depends(get_db)):
    return ClinicalSessionService(
        ClinicalSessionRepository(db)
    )


@router.post("")
async def create_session(
    payload: ClinicalSessionCreate,
    service=Depends(get_service),
    user=Depends(get_current_user),
):
    return await service.create(payload, user["org"])