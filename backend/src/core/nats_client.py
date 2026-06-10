"""
NetWatch AI — NATS Connection Manager
NATS JetStream client for inter-service messaging.
"""

import logging
from typing import Optional

import nats
from nats.aio.client import Client as NATSClient
from nats.js import JetStreamContext

from src.core.config import settings

logger = logging.getLogger("netwatch.nats")

nc: Optional[NATSClient] = None
js: Optional[JetStreamContext] = None


async def nats_error_cb(e):
    logger.debug(f"NATS connection error: {e}")


async def init_nats() -> tuple[NATSClient, JetStreamContext]:
    """Initialize NATS connection and create JetStream stream."""
    global nc, js

    nc = await nats.connect(
        settings.NATS_URL,
        max_reconnect_attempts=1,
        connect_timeout=3,
        error_cb=nats_error_cb,
    )
    js = nc.jetstream()

    # Create the main netwatch stream (idempotent — safe to call multiple times)
    try:
        await js.add_stream(
            name="netwatch",
            subjects=["netwatch.>"],
            retention="limits",
            max_msgs=1_000_000,
            max_bytes=256 * 1024 * 1024,  # 256 MB max
        )
        logger.info("✅ NATS JetStream stream 'netwatch' created/verified")
    except Exception as e:
        logger.warning(f"JetStream stream setup: {e}")

    logger.info(f"✅ NATS connected at {settings.NATS_URL}")
    return nc, js


async def close_nats():
    """Close the NATS connection."""
    global nc, js
    if nc:
        await nc.close()
        nc = None
        js = None
        logger.info("NATS connection closed")


async def get_nats() -> NATSClient:
    """Dependency injection for NATS client."""
    if not nc:
        raise RuntimeError("NATS not initialized — call init_nats() first")
    return nc


async def get_jetstream() -> JetStreamContext:
    """Dependency injection for JetStream context."""
    if not js:
        raise RuntimeError("JetStream not initialized — call init_nats() first")
    return js
