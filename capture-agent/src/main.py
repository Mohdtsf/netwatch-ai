"""
NetWatch AI — Capture Agent
Main entrypoint for the packet capture and network discovery service.
"""

import asyncio
import json
import logging
import os
import signal
import sys

from src.sniffer import PacketSniffer
from src.dns_extractor import DnsExtractor
from src.sni_extractor import SniExtractor
from src.flow_assembler import FlowAssembler
from src.geoip import GeoIPEnricher
from src.mac_vendor import MacVendorLookup
from src.nats_producer import NatsProducer
from src.arp_scanner import ArpScanner
from src.dhcp_parser import DhcpParser

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

    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("Received shutdown signal")
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    # Initialize components
    nats = NatsProducer(url=NATS_URL)
    await nats.connect()

    geoip = GeoIPEnricher()
    geoip.load()

    mac_vendor = MacVendorLookup()
    mac_vendor.load()

    dns = DnsExtractor()
    sni = SniExtractor()
    flows = FlowAssembler()

    sniffer = PacketSniffer(interface=CAPTURE_INTERFACE)
    sniffer.add_handler(dns.process)
    sniffer.add_handler(sni.process)
    sniffer.add_handler(flows.process)

    arp = ArpScanner(subnet=SCAN_SUBNET, interface=CAPTURE_INTERFACE)
    dhcp = DhcpParser()

    # Background tasks
    async def arp_loop():
        while not stop_event.is_set():
            devices = await arp.scan()
            devices.extend(arp.read_arp_cache())
            
            seen_macs = set()
            unique_devices = []
            hostnames = dhcp.get_hostnames()
            
            for dev in devices:
                mac = dev["mac"].lower()
                if mac not in seen_macs:
                    seen_macs.add(mac)
                    dev["mac"] = mac
                    dev["vendor"] = mac_vendor.lookup(mac)
                    if mac in hostnames:
                        dev["hostname"] = hostnames[mac]
                    unique_devices.append(dev)
                    
            for dev in unique_devices:
                if nats.connected:
                    await nats.publish("netwatch.devices.events", json.dumps(dev).encode('utf-8'))
            try:
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break

    async def flow_flush_loop():
        while not stop_event.is_set():
            expired = flows.flush_expired()
            for flow in expired:
                # Enrich with Domain
                if not flow.domain:
                    flow.domain = dns.lookup(flow.dst_ip)
                
                # Enrich with GeoIP
                country, asn = geoip.lookup(flow.dst_ip)
                if country:
                    flow.country = country
                if asn:
                    flow.asn = asn

                # Publish to NATS
                if nats.connected:
                    await nats.publish("netwatch.flows.raw", json.dumps(flow.to_dict()).encode('utf-8'))
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break

    await sniffer.start()
    logger.info("🚀 Capture Agent ready")

    arp_task = asyncio.create_task(arp_loop())
    flow_task = asyncio.create_task(flow_flush_loop())

    await stop_event.wait()
    logger.info("👋 Capture Agent stopping...")
    
    arp_task.cancel()
    flow_task.cancel()
    
    await sniffer.stop()
    await nats.close()
    geoip.close()
    
    logger.info("👋 Capture Agent stopped")


if __name__ == "__main__":
    asyncio.run(main())
