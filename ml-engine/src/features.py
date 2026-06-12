"""
NetWatch AI — Feature Extraction
Transforms raw flow data into ML-ready feature vectors.
"""

import logging
import time
from typing import Optional

import numpy as np

logger = logging.getLogger("netwatch.ml.features")

# Well-known ports for feature engineering
WELL_KNOWN_PORTS = {
    22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995,
    3306, 3389, 5432, 5900, 6379, 8080, 8443, 8888,
}

# Country risk scores (higher = riskier for home networks)
GEO_RISK_SCORES = {
    "US": 0.1, "GB": 0.1, "DE": 0.1, "FR": 0.1, "CA": 0.1,
    "AU": 0.1, "JP": 0.1, "NL": 0.1, "SE": 0.1, "NO": 0.1,
    "CN": 0.6, "RU": 0.7, "KP": 0.9, "IR": 0.7,
}


class FeatureExtractor:
    """Stateful feature extractor to calculate moving averages."""
    
    def __init__(self):
        self.ip_connection_count = {}
        self.ip_ports_seen = {}
        self.last_cleanup = time.time()
        
    def _cleanup_state(self):
        now = time.time()
        if now - self.last_cleanup > 300: # 5 mins cleanup
            self.ip_connection_count.clear()
            self.ip_ports_seen.clear()
            self.last_cleanup = now
            
    def _port_entropy(self, port: int) -> float:
        if port == 0:
            return 0.0
        if port < 1024:
            return 0.2
        elif port < 10000:
            return 0.5
        return 0.8

    def extract(self, flow: dict) -> np.ndarray:
        self._cleanup_state()
        
        src_ip = flow.get("src_ip", "0.0.0.0")
        dst_port = flow.get("dst_port", 0)
        
        self.ip_connection_count[src_ip] = self.ip_connection_count.get(src_ip, 0) + 1
        if src_ip not in self.ip_ports_seen:
            self.ip_ports_seen[src_ip] = set()
        self.ip_ports_seen[src_ip].add(dst_port)
        
        duration = max(flow.get("duration", 1.0), 0.001)
        bytes_total = flow.get("bytes", 0)
        packets = max(flow.get("packets", 1), 1)
        protocol = flow.get("protocol", "").upper()
        country = flow.get("country", "")

        conn_per_min = self.ip_connection_count[src_ip]
        unique_ports = len(self.ip_ports_seen[src_ip])

        vector = [
            bytes_total / duration,
            packets / duration,
            bytes_total / packets,
            self._port_entropy(dst_port),
            1.0 if dst_port in WELL_KNOWN_PORTS else 0.0,
            GEO_RISK_SCORES.get(country, 0.3),
            min(dst_port / 65535.0, 1.0),
            1.0 if protocol == "TCP" else 0.0,
            1.0 if protocol == "UDP" else 0.0,
            conn_per_min,
            unique_ports,
        ]
        return np.array([vector])
