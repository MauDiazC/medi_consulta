import json
import hashlib
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
from app.core.config import settings

class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Professional Idempotency Layer.
    Uses Redis to store response fingerprints for 24h.
    Requires header: X-Idempotency-Key
    """
    def __init__(self, app, redis_url: str):
        super().__init__(app)
        self.redis = redis.from_url(redis_url)
        self.ttl = 86400  # 24 hours

    async def dispatch(self, request: Request, call_next):
        # 1. Skip if not a write operation or missing header
        if request.method not in ["POST", "PATCH", "PUT"]:
            return await call_next(request)

        idempotency_key = request.headers.get("X-Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        # 2. Institutional Namespace
        user_id = getattr(request.state, "user_id", "anonymous")
        redis_key = f"idempotency:{user_id}:{idempotency_key}"

        # 3. Check for existing response
        cached_response = await self.redis.get(redis_key)
        if cached_response:
            data = json.loads(cached_response)
            return Response(
                content=data["body"],
                status_code=data["status_code"],
                headers=data["headers"],
                media_type=data["media_type"]
            )

        # 4. Execute Request
        response = await call_next(request)

        # 5. Only cache successful responses (2xx) or specific errors
        if 200 <= response.status_code < 300:
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # Store in Redis
            payload = {
                "body": response_body.decode("utf-8") if response_body else "",
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": response.media_type
            }
            await self.redis.setex(redis_key, self.ttl, json.dumps(payload))

            # Reconstruct response for the caller
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )

        return response
