
import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.locks import acquire_encounter_lock, release_encounter_lock
from app.core.config import settings
from app.core.events import get_redis

from .repository import WorkspaceRepository
from .service import WorkspaceService

router = APIRouter(
    prefix="/workspace",
    tags=["workspace"],
)


@router.get("/encounter/{encounter_id}")
async def encounter_workspace(
    encounter_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(
        WorkspaceRepository(db)
    )

    return await service.encounter_workspace(
        encounter_id,
        user["id"],
    )


@router.post("/lock/{encounter_id}")
async def lock_encounter(
    encounter_id: str,
    user=Depends(get_current_user),
):
    return await acquire_encounter_lock(
        encounter_id,
        user["id"],
    )


@router.post("/unlock/{encounter_id}")
async def unlock_encounter(
    encounter_id: str,
    user=Depends(get_current_user),
):
    return await release_encounter_lock(
        encounter_id,
        user["id"],
    )


@router.get("/stream/{encounter_id}")
async def workspace_stream(encounter_id: str):

    async def event_generator():
        r = get_redis()
        if r is None:
            yield "data: mock-event\n\n"
            return

        pubsub = r.pubsub()
        await pubsub.subscribe(
            f"workspace_updates:{encounter_id}"
        )

        async for message in pubsub.listen():
            if message["type"] == "message":
                yield f"data: {message['data'].decode()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )