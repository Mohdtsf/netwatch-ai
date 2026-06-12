"""
NetWatch AI — Threat Intelligence
Downloads and caches IP/domain blocklists from open threat feeds.
"""

import logging
import os
import asyncio
import httpx
from redis.asyncio import Redis

logger = logging.getLogger("netwatch.ml.threat_intel")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

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

    def __init__(self, redis_url: str = REDIS_URL):
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self._last_updated = None

    async def update(self):
        """Download and cache all threat feeds."""
        logger.info("Downloading threat intel feeds...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = [
                self._download_and_store(client, name, url)
                for name, url in FEEDS.items()
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        from datetime import datetime
        self._last_updated = datetime.utcnow().isoformat()
        logger.info("Threat intel update complete")

    async def _download_and_store(self, client: httpx.AsyncClient, name: str, url: str):
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            lines = resp.text.splitlines()
            count = 0
            
            pipeline = self.redis.pipeline()
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                if name == "abuse_ch_domains":
                    import urllib.parse
                    try:
                        parsed = urllib.parse.urlparse(line.strip('"'))
                        if parsed.netloc:
                            pipeline.setex(f"threat:domain:{parsed.netloc}", 86400, "malware")
                            count += 1
                    except Exception:
                        pass
                else:
                    pipeline.setex(f"threat:ip:{line}", 86400, "malware")
                    count += 1
                    
            await pipeline.execute()
            logger.info(f"Loaded {count} items from {name}")
            
        except Exception as e:
            logger.error(f"Failed to update feed {name}: {e}")

    async def check_ip(self, ip: str) -> bool:
        """Check if an IP is in any threat feed."""
        return await self.redis.exists(f"threat:ip:{ip}") > 0

    async def check_domain(self, domain: str) -> bool:
        """Check if a domain is in any threat feed."""
        if not domain:
            return False
        return await self.redis.exists(f"threat:domain:{domain}") > 0

    @property
    def stats(self) -> dict:
        return {
            "last_updated": self._last_updated,
        }
