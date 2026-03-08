import logging
import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging import configure_logging
from app.core.telemetry import setup_telemetry
from prometheus_fastapi_instrumentator import Instrumentator

from app.modules.auth.router import router as auth_router
from app.modules.clinical_sessions.router import \
    router as clinical_sessions_router
from app.modules.dictation.websocket import router as dictation_ws
from app.modules.encounters.router import router as encounters_router
from app.modules.health.router import router as health_router
from app.modules.notes.router import router as notes_router
from app.modules.notes.signing.router import router as note_sign_router
from app.modules.notes.signing.verifier_router import router as verify_router
from app.modules.organizations.router import router as organizations_router
from app.modules.patients.router import router as patients_router
from app.modules.users.router import router as users_router
from app.modules.workspace.router import router as workspace_router


def create_app() -> FastAPI:
    """
    Application factory with institutional structured logging.
    """
    configure_logging()
    logger = logging.getLogger("api")

    app = FastAPI(
        title="Mediconsulta API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @app.on_event("startup")
    async def startup_event():
        logger.info("Application starting up")
        setup_telemetry(app)
        
        # Redis connection for Rate Limiting
        try:
            r = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
            await FastAPILimiter.init(r)
            logger.info("Rate limiter initialized with Redis")
        except Exception as e:
            logger.error(f"Rate limiter failed to initialize: {e}")

        # 0) Supabase Institutional Configuration Guard
        supabase_url = getattr(settings, "SUPABASE_URL", None)
        supabase_key = getattr(settings, "SUPABASE_ANON_KEY", None)
        
        if not supabase_url or not supabase_key:
            raise RuntimeError(
                "CRITICAL CONFIGURATION MISSING: SUPABASE_URL and SUPABASE_ANON_KEY "
                "are required for identity and security services."
            )

        # 1) Database Health Check (Scoped session)
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            logger.info("Database connection established", extra={"status": "healthy"})
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}", exc_info=True, extra={"status": "unhealthy"})

        # 2) Redis Health Check (Transient connection)
        try:
            temp_r = redis.from_url(settings.REDIS_URL)
            await temp_r.ping()
            await temp_r.close()
            logger.info("Redis connection established", extra={"status": "healthy"})
        except Exception as e:
            logger.error(f"Redis initialization failed: {str(e)}", exc_info=True, extra={"status": "unhealthy"})

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Application shutting down")

    # --- CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], 
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize Prometheus Metrics
    Instrumentator().instrument(app).expose(app)

    # --- Routers
    app.include_router(health_router)
    app.include_router(organizations_router)
    app.include_router(users_router)
    app.include_router(patients_router)
    app.include_router(encounters_router)
    app.include_router(notes_router)
    app.include_router(auth_router)
    app.include_router(workspace_router)
    app.include_router(dictation_ws)
    app.include_router(clinical_sessions_router)
    app.include_router(note_sign_router)
    app.include_router(verify_router)

    return app


app = create_app()
