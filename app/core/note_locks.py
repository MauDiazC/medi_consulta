import json
from datetime import datetime, timedelta

import redis.asyncio as redis
from fastapi import HTTPException
from app.core.config import settings
from app.core.events import get_redis

LOCK_TTL = 120


async def acquire_note_lock(
    note_id: str,
    doctor_id: str,
    session_id: str,
):
    r = get_redis()
    if r is None:
        return {"locked": True}

    key = f"lock:note:{note_id}"

    existing = await r.get(key)

    if existing:
        data = json.loads(existing)

        # mismo doctor otra tab
        if data["doctor_id"] == doctor_id:
            if data["session_id"] != session_id:
                raise HTTPException(
                    409,
                    "Note already opened in another tab",
                )

        else:
            raise HTTPException(
                423,
                "Note locked by another clinician",
            )

    payload = {
        "doctor_id": doctor_id,
        "session_id": session_id,
        "expires_at": (
            datetime.utcnow()
            + timedelta(seconds=LOCK_TTL)
        ).isoformat(),
    }

    await r.set(
        key,
        json.dumps(payload),
        ex=LOCK_TTL,
    )

    return {"locked": True}


async def release_note_lock(
    note_id: str,
    doctor_id: str,
    session_id: str,
):
    r = get_redis()
    if r is None:
        return {"released": True}

    key = f"lock:note:{note_id}"

    existing = await r.get(key)

    if not existing:
        return {"released": True}

    data = json.loads(existing)

    if (
        data["doctor_id"] != doctor_id
        or data["session_id"] != session_id
    ):
        raise HTTPException(
            403,
            "Invalid lock owner",
        )

    await r.delete(key)

    return {"released": True}