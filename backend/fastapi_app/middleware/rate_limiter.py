import time

import redis.asyncio as aioredis
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from shared.config import get_settings

settings = get_settings()

RATE_LIMIT_LUA_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""

EXEMPT_PATHS = {"/health", "/ready", "/docs", "/redoc", "/openapi.json"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str = "redis://localhost:6379/0"):
        super().__init__(app)
        self.redis_url = redis_url
        self._redis = None
        self._script_sha = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path

        if path in EXEMPT_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        # Extract identity from authorization header if present
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return await call_next(request)

        # Use token hash as rate limit key (avoids full JWT decode in middleware)
        token = auth_header[7:]
        identity = token[-16:] if len(token) > 16 else token

        org_id = request.headers.get("x-organization-id", "default")
        key_base = f"rate:{org_id}:{identity}"

        try:
            r = await self._get_redis()

            now_minute = int(time.time() // 60)
            now_hour = int(time.time() // 3600)

            minute_key = f"{key_base}:m:{now_minute}"
            hour_key = f"{key_base}:h:{now_hour}"

            pipe = r.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 120)
            pipe.incr(hour_key)
            pipe.expire(hour_key, 7200)
            results = await pipe.execute()

            minute_count = results[0]
            hour_count = results[2]

            per_minute = settings.rate_limit_default_per_minute
            per_hour = settings.rate_limit_default_per_hour

            response = await call_next(request)

            response.headers["X-RateLimit-Limit-Minute"] = str(per_minute)
            response.headers["X-RateLimit-Remaining-Minute"] = str(
                max(0, per_minute - minute_count)
            )
            response.headers["X-RateLimit-Limit-Hour"] = str(per_hour)
            response.headers["X-RateLimit-Remaining-Hour"] = str(
                max(0, per_hour - hour_count)
            )

            if minute_count > per_minute:
                retry_after = 60 - (int(time.time()) % 60)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again later."},
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit-Minute": str(per_minute),
                        "X-RateLimit-Remaining-Minute": "0",
                    },
                )

            if hour_count > per_hour:
                retry_after = 3600 - (int(time.time()) % 3600)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Hourly rate limit exceeded. Try again later."},
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit-Hour": str(per_hour),
                        "X-RateLimit-Remaining-Hour": "0",
                    },
                )

            return response

        except Exception:
            # If Redis is unavailable, allow the request through
            return await call_next(request)
