"""
NetWatch AI — Capture Agent
Main entrypoint for the packet capture and network discovery service.

This service runs with network_mode: host and CAP_NET_RAW to:
1. Capture packets in promiscuous mode via Scapy
2. Extract DNS queries and TLS SNI fields
3. Assemble flows (5-tuple grouping)
4. Enrich with GeoIP and MAC vendor data
5. Publish enriched flows to NATS JetStream
6. Run periodic ARP scans for device discovery
"""

import asyncio
import logging
import os
import signal
import sys

logger = logging.getLogger("netwatch.capture")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

# Capture agent configuration from environment
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
CAPTURE_INTERFACE = os.getenv("CAPTURE_INTERFACE", "eth0")
SCAN_SUBNET = os.getenv("SCAN_SUBNET", "192.168.1.0/24")


async def main():
    """Main capture agent loop."""
    logger.info("═" * 50)
    logger.info("  NetWatch AI — Capture Agent Starting")
    logger.info(f"  Interface: {CAPTURE_INTERFACE}")
    logger.info(f"  Subnet:    {SCAN_SUBNET}")
    logger.info(f"  NATS:      {NATS_URL}")
    logger.info("═" * 50)

    # TODO Phase 3: Initialize NATS connection
    # TODO Phase 3: Start Scapy sniffer in background thread
    # TODO Phase 3: Start flow assembler
    # TODO Phase 3: Start ARP scanner (every 30 seconds)
    # TODO Phase 4: Start mDNS listener
    # TODO Phase 4: Start SSDP/UPnP discovery

    logger.info("🚀 Capture Agent ready (stub — waiting for Phase 3)")

    # Keep the agent running
    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("Received shutdown signal")
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    await stop_event.wait()
    logger.info("👋 Capture Agent stopped")


if __name__ == "__main__":
    asyncio.run(main())
