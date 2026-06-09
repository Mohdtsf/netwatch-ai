"""
NetWatch AI — Threat Intelligence
Downloads and caches IP/domain blocklists from open threat feeds.
"""

import logging
import os
from typing import Set

logger = logging.getLogger("netwatch.ml.threat_intel")

# Free threat intelligence feed URLs
FEEDS = {
    "abuse_ch_ips": "https://feodotracker.abuse.ch/downloads/ipblocklist.txt",
    "abuse_ch_domains": "https://urlhaus.abuse.ch/downloads/text_online/",
    "emerging_threats": "https://rules.emergingthreats.net/blockrules/compromised-ips.txt",
}


class ThreatIntelManager:
    """
    Manages threat intelligence feeds.
    
    Downloads IP and domain blocklists from free sources:
    - abuse.ch (Feodo Tracker — botnet IPs)
    - URLhaus (malware distribution URLs)
    - Emerging Threats (compromised IPs)
    
    Caches in Redis for O(1) lookup during flow processing.
    """

    def __init__(self):
        self._malicious_ips: Set[str] = set()
        self._malicious_domains: Set[str] = set()
        self._last_updated = None

    async def update(self):
        """Download and cache all threat feeds. TODO Phase 8."""
        logger.info("Threat intel update stub — waiting for Phase 8")

    def check_ip(self, ip: str) -> bool:
        """Check if an IP is in any threat feed."""
        return ip in self._malicious_ips

    def check_domain(self, domain: str) -> bool:
        """Check if a domain is in any threat feed."""
        return domain in self._malicious_domains

    @property
    def stats(self) -> dict:
        return {
            "malicious_ips": len(self._malicious_ips),
            "malicious_domains": len(self._malicious_domains),
            "last_updated": self._last_updated,
        }
