"""
NetWatch AI — Flow Assembler
Groups packets into network flows by 5-tuple (src_ip, dst_ip, src_port, dst_port, protocol).
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("netwatch.capture.flow")


@dataclass
class Flow:
    """A network flow — a group of related packets between two endpoints."""
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    bytes: int = 0
    packets: int = 0
    start_time: float = field(default_factory=time.time)
    last_time: float = field(default_factory=time.time)
    domain: Optional[str] = None
    country: Optional[str] = None
    asn: Optional[str] = None

    @property
    def duration(self) -> float:
        return max(self.last_time - self.start_time, 0.001)

    @property
    def flow_key(self) -> str:
        return f"{self.src_ip}:{self.src_port}->{self.dst_ip}:{self.dst_port}/{self.protocol}"

    def to_dict(self) -> dict:
        return {
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "protocol": self.protocol,
            "bytes": self.bytes,
            "packets": self.packets,
            "duration": round(self.duration, 3),
            "domain": self.domain,
            "country": self.country,
            "asn": self.asn,
            "time": int(self.start_time),
        }


class FlowAssembler:
    """
    Assembles packets into flows with a configurable timeout.
    
    Flows are groups of packets sharing the same 5-tuple.
    When a flow hasn't received a new packet for `timeout` seconds,
    it's considered complete and emitted for processing.
    """

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._active_flows: dict[str, Flow] = {}
        self._flow_count = 0

    def process(self, packet) -> Optional[Flow]:
        """
        Process a packet and return a completed flow if the timeout expired.
        TODO Phase 3: Implement with Scapy packet parsing.
        """
        pass

    def flush_expired(self) -> list[Flow]:
        """Flush all flows that have exceeded the timeout."""
        now = time.time()
        expired = []
        expired_keys = []

        for key, flow in self._active_flows.items():
            if now - flow.last_time > self.timeout:
                expired.append(flow)
                expired_keys.append(key)

        for key in expired_keys:
            del self._active_flows[key]

        self._flow_count += len(expired)
        return expired

    @property
    def stats(self) -> dict:
        return {
            "active_flows": len(self._active_flows),
            "completed_flows": self._flow_count,
        }
