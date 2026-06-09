"""
NetWatch AI — NATS Consumer for ML Engine
Consumes enriched flows from NATS and runs ML inference.
"""

import logging
import os

logger = logging.getLogger("netwatch.ml.nats_consumer")

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")


class MLNatsConsumer:
    """
    Consumes enriched flow data from NATS JetStream and runs:
    1. Feature extraction
    2. Isolation Forest anomaly scoring
    3. Random Forest threat classification (if anomaly detected)
    4. Threat intel IP/domain checking
    5. Alert publishing to NATS alerts topic
    
    TODO Phase 8: Full implementation
    """

    def __init__(self, url: str = NATS_URL):
        self.url = url
        self._nc = None
        self._js = None
        self._sub = None

    async def start(self):
        """Connect to NATS and subscribe to enriched-flows."""
        logger.info("ML NATS consumer stub — waiting for Phase 8")

    async def stop(self):
        """Stop consuming and close connection."""
        if self._sub:
            await self._sub.unsubscribe()
        if self._nc:
            await self._nc.close()
