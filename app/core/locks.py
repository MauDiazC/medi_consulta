import json
from datetime import datetime, timedelta

import redis.asyncio as redis
from fastapi import HTTPException
from app.core.config import settings
from app.core.events import get_redis

LOCK_TTL = 120  # seconds


async def acquire_encounter_lock(
    encounter_id: str,
    doctor_id: str,
):
    r = get_redis()
    if r is None:
        return {"locked": True}

    key = f"lock:encounter:{encounter_id}"

    existing = await r.get(key)

    if existing:
        data = json.loads(existing)

        if data["doctor_id"] != doctor_id:
            raise HTTPException(
                423,
                "Encounter is currently being edited by another clinician",
            )

    payload = {
        "doctor_id": doctor_id,
        "expires_at": (
            datetime.utcnow() +
            timedelta(seconds=LOCK_TTL)
        ).isoformat(),
    }

    await r.set(
        key,
        json.dumps(payload),
        ex=LOCK_TTL,
    )

    return {"locked": True}


async def release_encounter_lock(
    encounter_id: str,
    doctor_id: str,
):
    r = get_redis()
    if r is None:
        return {"released": True}

    key = f"lock:encounter:{encounter_id}"

    existing = await r.get(key)

    if not existing:
        return {"released": True}

    data = json.loads(existing)

    if data["doctor_id"] != doctor_id:
        raise HTTPException(
            403,
            "Cannot release another clinician's lock",
        )

    await r.delete(key)

    return {"released": True}