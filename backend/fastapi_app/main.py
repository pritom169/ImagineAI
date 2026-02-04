from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi_app.api.v1.router import api_router
from fastapi_app.api.websocket import ws_router
from fastapi_app.middleware.request_id import RequestIDMiddleware
from shared.config import get_settings
from shared.database import engine
from shared.exceptions import ImagineAIError

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    yield
    # Shutdown
    await app.state.redis.close()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="AI-Powered E-Commerce Image Intelligence Platform",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4200"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIDMiddleware)

    from fastapi_app.middleware.rate_limiter import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware, redis_url=settings.redis_url)

    # Exception handlers
    @app.exception_handler(ImagineAIError)
    async def imagineai_error_handler(request: Request, exc: ImagineAIError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    # Routes
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(ws_router)

    # Health checks
    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    @app.get("/ready")
    async def ready(request: Request):
        checks = {}
        # Check database
        try:
            from shared.database import async_session_factory
            from sqlalchemy import text

            async with async_session_factory() as session:
                await session.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"error: {e}"

        # Check Redis
        try:
            await request.app.state.redis.ping()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {e}"

        all_ok = all(v == "ok" for v in checks.values())
        return JSONResponse(
            status_code=200 if all_ok else 503,
            content={"status": "ready" if all_ok else "not_ready", "checks": checks},
        )

    return app


app = create_app()
