"""
NetWatch AI — Scapy Packet Sniffer
Captures packets in promiscuous mode and extracts flow data.
"""

import logging
from typing import Callable, Optional
from scapy.all import AsyncSniffer

logger = logging.getLogger("netwatch.capture.sniffer")


class PacketSniffer:
    """
    High-performance packet capture using Scapy.
    
    Captures packets on the specified interface in promiscuous mode,
    applies BPF filters, and passes each packet to registered handlers.
    """

    def __init__(self, interface: str = "eth0", bpf_filter: str = ""):
        self.interface = interface
        self.bpf_filter = bpf_filter or self._default_filter()
        self.handlers: list[Callable] = []
        self._running = False
        self._packet_count = 0
        self._sniffer: Optional[AsyncSniffer] = None

    def _default_filter(self) -> str:
        """Default BPF filter: skip localhost and broadcast noise."""
        return "not (src host 127.0.0.1 and dst host 127.0.0.1) and ip"

    def add_handler(self, handler: Callable):
        """Register a packet processing handler."""
        self.handlers.append(handler)

    def _packet_callback(self, packet):
        self._packet_count += 1
        if self._packet_count % 100 == 0:
            logger.info(f"Captured {self._packet_count} packets...")
            
        for handler in self.handlers:
            try:
                handler(packet)
            except Exception as e:
                logger.error(f"Error in handler {handler}: {e}")

    async def start(self):
        """Start packet capture. Runs in a background thread."""
        logger.info(f"Starting Scapy AsyncSniffer on {self.interface} with filter '{self.bpf_filter}'")
        self._sniffer = AsyncSniffer(
            iface=self.interface,
            filter=self.bpf_filter,
            prn=self._packet_callback,
            store=False,
            promisc=True
        )
        self._sniffer.start()
        self._running = True

    async def stop(self):
        """Stop packet capture."""
        self._running = False
        if self._sniffer:
            self._sniffer.stop()
            self._sniffer.join()
        logger.info(f"Sniffer stopped. Captured {self._packet_count} packets.")

    @property
    def stats(self) -> dict:
        return {
            "interface": self.interface,
            "running": self._running,
            "packets_captured": self._packet_count,
        }
