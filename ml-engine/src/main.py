"""
NetWatch AI — ML Inference Engine
FastAPI service for anomaly detection, threat classification, and device fingerprinting.

Models:
- Isolation Forest: anomaly detection on network flows
- Random Forest: threat classification (PortScan, DDoS, BruteForce, etc.)
- HDBSCAN: device type clustering from traffic patterns
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

logger = logging.getLogger("netwatch.ml")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """ML engine startup and shutdown."""
    logger.info("═" * 50)
    logger.info("  NetWatch AI — ML Engine Starting")
    logger.info("═" * 50)

    # TODO Phase 8: Load trained models from disk
    # TODO Phase 8: Connect to NATS for enriched-flows consumption
    # TODO Phase 8: Connect to Redis for threat intel cache
    # TODO Phase 8: Load threat intel feeds

    logger.info("🚀 ML Engine ready (stub — waiting for Phase 8)")
    yield

    logger.info("👋 ML Engine stopped")


app = FastAPI(
    title="NetWatch AI — ML Engine",
    description="Anomaly detection and threat classification",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)


@app.get("/health", tags=["system"])
async def health_check():
    """ML engine health check."""
    return {
        "status": "healthy",
        "service": "netwatch-ml-engine",
        "version": "0.1.0",
        "models_loaded": False,  # TODO: update when models are loaded
    }


@app.get("/api/v1/ml/status", tags=["ml"])
async def ml_status():
    """Get ML engine status and model info."""
    return {
        "models": {
            "isolation_forest": {"loaded": False, "version": None},
            "random_forest": {"loaded": False, "version": None},
            "hdbscan": {"loaded": False, "version": None},
        },
        "threat_intel": {
            "last_updated": None,
            "sources": ["abuse.ch", "feodo", "urlhaus"],
        },
    }
