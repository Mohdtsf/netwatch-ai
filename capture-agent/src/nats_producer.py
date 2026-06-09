"""
NetWatch AI — NATS Producer
Publishes enriched flow data to NATS JetStream topics.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger("netwatch.capture.nats")

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")


class NatsProducer:
    """
    Publishes messages to NATS JetStream.
    
    Topics:
    - raw-flows: Raw captured flow data
    - enriched-flows: Flows enriched with GeoIP, domain, vendor
    - device-events: New device discovered, device left network
    """

    STREAM_NAME = "netwatch"
    SUBJECTS = {
        "raw_flows": "netwatch.flows.raw",
        "enriched_flows": "netwatch.flows.enriched",
        "device_events": "netwatch.devices.events",
        "alerts": "netwatch.alerts",
    }

    def __init__(self, url: str = NATS_URL):
        self.url = url
        self._nc = None
        self._js = None
        self._connected = False

    async def connect(self):
        """Connect to NATS and initialize JetStream."""
        try:
            import nats

            self._nc = await nats.connect(self.url)
            self._js = self._nc.jetstream()

            # Create stream if it doesn't exist
            try:
                await self._js.add_stream(
                    name=self.STREAM_NAME,
                    subjects=["netwatch.>"],
                    retention="limits",
                    max_age=86400 * 1_000_000_000,  # 1 day in nanoseconds
                    storage="file",
                )
            except Exception:
                pass  # Stream already exists

            self._connected = True
            logger.info(f"✅ Connected to NATS at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            self._connected = False

    async def publish(self, subject: str, data: bytes):
        """Publish a message to a NATS subject."""
        if not self._connected or not self._js:
            logger.warning("NATS not connected, dropping message")
            return

        try:
            await self._js.publish(subject, data)
        except Exception as e:
            logger.error(f"NATS publish error: {e}")

    async def close(self):
        """Close the NATS connection."""
        if self._nc:
            await self._nc.close()
            self._connected = False
            logger.info("NATS connection closed")

    @property
    def connected(self) -> bool:
        return self._connected
