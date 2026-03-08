from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user

from .repository import TimelineRepository

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/patient/{patient_id}")
async def patient_timeline(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    repo = TimelineRepository(db)
    return await repo.patient_timeline(patient_id)
