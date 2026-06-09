"""
NetWatch AI — FastAPI Backend
Main application entrypoint with lifespan context manager.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from src.core.config import settings
from src.core.database import init_db, close_db

logger = logging.getLogger("netwatch")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle."""
    logger.info("═" * 50)
    logger.info("  NetWatch AI — Starting Backend")
    logger.info(f"  Profile: {settings.NETWATCH_PROFILE}")
    logger.info("═" * 50)

    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")

    # TODO Phase 3: Connect to NATS
    # TODO Phase 2: Start APScheduler
    # TODO Phase 2: Connect to Redis

    logger.info("🚀 Backend ready")
    yield

    # Shutdown
    logger.info("Shutting down...")
    await close_db()
    logger.info("👋 Backend stopped")


app = FastAPI(
    title="NetWatch AI",
    description="Self-hosted network security platform",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ──────────────────────────────


@app.get("/health", tags=["system"])
async def health_check():
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "service": "netwatch-backend",
        "version": "0.1.0",
        "profile": settings.NETWATCH_PROFILE,
    }


@app.get("/api/v1/system/info", tags=["system"])
async def system_info():
    """System information endpoint."""
    return {
        "name": "NetWatch AI",
        "version": "0.1.0",
        "profile": settings.NETWATCH_PROFILE,
        "ml_enabled": settings.ML_ENABLED,
    }
