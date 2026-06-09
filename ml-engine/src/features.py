"""
NetWatch AI — Feature Extraction
Transforms raw flow data into ML-ready feature vectors.
"""

import logging
import math
from typing import Optional

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


def extract_flow_features(flow: dict) -> list[float]:
    """
    Extract feature vector from a flow dict.
    
    Features:
    0. bytes_per_second
    1. packets_per_second
    2. byte_ratio (bytes / packets)
    3. port_entropy
    4. is_well_known_port (0 or 1)
    5. geo_risk_score
    6. dst_port (normalized)
    7. protocol_tcp (0 or 1)
    8. protocol_udp (0 or 1)
    """
    duration = max(flow.get("duration", 1), 0.001)
    bytes_total = flow.get("bytes", 0)
    packets = max(flow.get("packets", 1), 1)
    dst_port = flow.get("dst_port", 0)
    protocol = flow.get("protocol", "").upper()
    country = flow.get("country", "")

    return [
        bytes_total / duration,                          # bytes/sec
        packets / duration,                               # packets/sec
        bytes_total / packets,                            # bytes/packet
        _port_entropy(dst_port),                          # port entropy
        1.0 if dst_port in WELL_KNOWN_PORTS else 0.0,    # known port
        GEO_RISK_SCORES.get(country, 0.3),                # geo risk
        min(dst_port / 65535.0, 1.0),                     # normalized port
        1.0 if protocol == "TCP" else 0.0,                # is TCP
        1.0 if protocol == "UDP" else 0.0,                # is UDP
    ]


def _port_entropy(port: int) -> float:
    """Calculate a simple entropy proxy for the port number."""
    if port == 0:
        return 0.0
    # Higher entropy for unusual ports
    if port < 1024:
        return 0.2
    elif port < 10000:
        return 0.5
    else:
        return 0.8
