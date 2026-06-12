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
import asyncio

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from .nats_consumer import MLNatsConsumer
from .threat_intel import ThreatIntelManager
from .models.hdbscan_device import DeviceFingerprinter

logger = logging.getLogger("netwatch.ml")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

threat_intel = ThreatIntelManager()
nats_consumer = MLNatsConsumer(threat_intel=threat_intel)
hdbscan_model = DeviceFingerprinter()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """ML engine startup and shutdown."""
    logger.info("═" * 50)
    logger.info("  NetWatch AI — ML Engine Starting")
    logger.info("═" * 50)

    # Start threat intel download task (background)
    asyncio.create_task(threat_intel.update())

    # Start NATS consumer
    await nats_consumer.start()
    
    # Load batch model
    hdbscan_model.load()

    logger.info("🚀 ML Engine ready")
    yield

    logger.info("👋 ML Engine stopped")
    await nats_consumer.stop()


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
        "models_loaded": nats_consumer.anomaly_detector.is_loaded,
    }


@app.get("/api/v1/ml/status", tags=["ml"])
async def ml_status():
    """Get ML engine status and model info."""
    return {
        "models": {
            "isolation_forest": {"loaded": nats_consumer.anomaly_detector.is_loaded, "version": "0.1.0"},
            "random_forest": {"loaded": nats_consumer.threat_classifier.is_loaded, "version": "0.1.0"},
            "hdbscan": {"loaded": hdbscan_model.is_loaded, "version": "0.1.0"},
        },
        "threat_intel": threat_intel.stats,
    }
