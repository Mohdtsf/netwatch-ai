"""
NetWatch AI — Scapy Packet Sniffer
Captures packets in promiscuous mode and extracts flow data.
"""

import logging
from typing import Callable, Optional

logger = logging.getLogger("netwatch.capture.sniffer")


class PacketSniffer:
    """
    High-performance packet capture using Scapy.
    
    Captures packets on the specified interface in promiscuous mode,
    applies BPF filters, and passes each packet to registered handlers.
    
    Usage:
        sniffer = PacketSniffer(interface="eth0")
        sniffer.add_handler(dns_extractor.process)
        sniffer.add_handler(sni_extractor.process)
        sniffer.add_handler(flow_assembler.process)
        await sniffer.start()
    """

    def __init__(self, interface: str = "eth0", bpf_filter: str = ""):
        self.interface = interface
        self.bpf_filter = bpf_filter or self._default_filter()
        self.handlers: list[Callable] = []
        self._running = False
        self._packet_count = 0

    def _default_filter(self) -> str:
        """Default BPF filter: skip localhost and broadcast noise."""
        return "not (src host 127.0.0.1 and dst host 127.0.0.1)"

    def add_handler(self, handler: Callable):
        """Register a packet processing handler."""
        self.handlers.append(handler)

    async def start(self):
        """Start packet capture. Runs in a background thread."""
        # TODO Phase 3: Implement with scapy.sniff()
        logger.info(f"Sniffer stub ready on {self.interface}")
        self._running = True

    async def stop(self):
        """Stop packet capture."""
        self._running = False
        logger.info(f"Sniffer stopped. Captured {self._packet_count} packets.")

    @property
    def stats(self) -> dict:
        return {
            "interface": self.interface,
            "running": self._running,
            "packets_captured": self._packet_count,
        }
