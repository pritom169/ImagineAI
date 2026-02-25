import json
import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy import select

from shared.config import get_settings
from shared.database import async_session_factory
from shared.models.pipeline import ProcessingJob
from shared.models.user import User

settings = get_settings()
ws_router = APIRouter()


async def authenticate_websocket(token: str) -> uuid.UUID | None:
    """Validate JWT token from WebSocket query parameter."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        return uuid.UUID(user_id)
    except (JWTError, ValueError):
        return None


async def verify_job_ownership(job_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Check that the user owns the processing job."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(ProcessingJob.id).where(
                ProcessingJob.id == job_id,
                ProcessingJob.user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None


@ws_router.websocket("/ws/processing/{job_id}")
async def processing_websocket(
    websocket: WebSocket,
    job_id: uuid.UUID,
    token: str = Query(...),
):
    # Authenticate
    user_id = await authenticate_websocket(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid or missing token")
        return

    # Verify ownership
    if not await verify_job_ownership(job_id, user_id):
        await websocket.close(code=4003, reason="Access denied")
        return

    await websocket.accept()

    # Subscribe to Redis pub/sub channel for this job
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis_client.pubsub()
    channel = f"job:{job_id}"
    await pubsub.subscribe(channel)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])

                # Check if this is a terminal message
                try:
                    data = json.loads(message["data"])
                    if data.get("type") in ("job_complete", "job_failed"):
                        break
                except json.JSONDecodeError:
                    pass
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await redis_client.close()
