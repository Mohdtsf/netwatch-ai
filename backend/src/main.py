"""
NetWatch AI — FastAPI Backend
Main application entrypoint with full lifespan context manager.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from slowapi.errors import RateLimitExceeded
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from pydantic import BaseModel

from src.core.config import settings
from src.core.database import init_db, close_db
from src.core.rate_limit import limiter, _rate_limit_exceeded_handler

logger = logging.getLogger("netwatch")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

class CsrfSettings(BaseModel):
    secret_key: str = settings.JWT_SECRET_KEY
    cookie_samesite: str = "lax"

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle."""
    logger.info("═" * 50)
    logger.info("  NetWatch AI — Starting Backend")
    logger.info(f"  Profile: {settings.NETWATCH_PROFILE}")
    logger.info("═" * 50)

    # ── Startup ────────────────────────────────

    # 1. Initialize database
    await init_db()
    logger.info("✅ Database initialized")

    # 2. Connect to Redis
    try:
        from src.core.redis import init_redis
        await init_redis()
    except Exception as e:
        logger.warning(f"⚠️  Redis connection failed (rate limiting/sessions disabled): {e}")

    # 3. Connect to NATS
    try:
        from src.core.nats_client import init_nats
        await init_nats()
        
        # Start Flow Consumer
        from src.flows.consumer import flow_consumer
        await flow_consumer.start()
        
        # Start Device Processor
        from src.devices.processor import device_processor
        await device_processor.start()
        
    except Exception as e:
        logger.warning(f"⚠️  NATS connection failed (messaging disabled): {e}")

    # 4. Start APScheduler
    from src.core.scheduler import start_scheduler
    await start_scheduler()
    logger.info("✅ APScheduler started")

    logger.info("🚀 Backend ready — all services initialized")
    yield

    # ── Shutdown ───────────────────────────────
    logger.info("Shutting down...")

    from src.core.scheduler import stop_scheduler
    await stop_scheduler()

    try:
        from src.flows.consumer import flow_consumer
        await flow_consumer.stop()
        
        from src.devices.processor import device_processor
        await device_processor.stop()
        
        from src.core.nats_client import close_nats
        await close_nats()
    except Exception:
        pass

    try:
        from src.core.redis import close_redis
        await close_redis()
    except Exception:
        pass

    await close_db()
    logger.info("👋 Backend stopped")


app = FastAPI(
    title="NetWatch AI",
    description="Self-hosted network security platform — live traffic monitoring, DNS firewall, "
                "device tracker, AI anomaly detection, WireGuard VPN.",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ─────────────────────────────────

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CSRF
@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    return ORJSONResponse(status_code=exc.status_code, content={"detail": exc.message})

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ──────────────────────────

from src.auth.router import router as auth_router
from src.devices.router import router as devices_router
from src.flows.router import router as flows_router
from src.alerts.router import router as alerts_router
from src.core.websocket import router as ws_router

app.include_router(auth_router)
app.include_router(devices_router)
app.include_router(flows_router)
app.include_router(alerts_router)
app.include_router(ws_router)


# ── Health Check ──────────────────────────────


@app.get("/health", tags=["system"])
async def health_check():
    """Service health check endpoint."""
    health = {
        "status": "healthy",
        "service": "netwatch-backend",
        "version": "0.1.0",
        "profile": settings.NETWATCH_PROFILE,
        "components": {},
    }

    # Check Redis
    try:
        from src.core.redis import redis_client
        if redis_client:
            await redis_client.ping()
            health["components"]["redis"] = "connected"
        else:
            health["components"]["redis"] = "not initialized"
    except Exception:
        health["components"]["redis"] = "disconnected"

    # Check NATS
    try:
        from src.core.nats_client import nc
        if nc and nc.is_connected:
            health["components"]["nats"] = "connected"
        else:
            health["components"]["nats"] = "not initialized"
    except Exception:
        health["components"]["nats"] = "disconnected"

    # Check database
    try:
        from src.core.database import async_session
        from sqlalchemy import text
        async with async_session() as db:
            await db.execute(text("SELECT 1"))
        health["components"]["database"] = "connected"
    except Exception:
        health["components"]["database"] = "disconnected"
        health["status"] = "degraded"

    # Check scheduler
    from src.core.scheduler import scheduler
    health["components"]["scheduler"] = "running" if scheduler.running else "stopped"

    return health


@app.get("/api/v1/system/info", tags=["system"])
async def system_info():
    """System information endpoint."""
    return {
        "name": "NetWatch AI",
        "version": "0.1.0",
        "profile": settings.NETWATCH_PROFILE,
        "ml_enabled": settings.ML_ENABLED,
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "websocket_live": "/ws/live",
            "websocket_alerts": "/ws/alerts",
        },
    }
