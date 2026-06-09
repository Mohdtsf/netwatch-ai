"""
NetWatch AI — GeoIP Enricher
Maps IP addresses to countries and ASNs using MaxMind GeoLite2.
"""

import logging
import os
from typing import Optional, Tuple

logger = logging.getLogger("netwatch.capture.geoip")

# GeoLite2 database paths
GEOIP_CITY_PATH = os.getenv("GEOIP_CITY_PATH", "/app/data/GeoLite2-City.mmdb")
GEOIP_ASN_PATH = os.getenv("GEOIP_ASN_PATH", "/app/data/GeoLite2-ASN.mmdb")


class GeoIPEnricher:
    """
    Enriches IP addresses with geographic and ASN information.
    Uses MaxMind GeoLite2 databases (free, updated monthly).
    """

    def __init__(self):
        self._city_reader = None
        self._asn_reader = None
        self._loaded = False

    def load(self):
        """Load GeoIP databases from disk."""
        try:
            import geoip2.database

            if os.path.exists(GEOIP_CITY_PATH):
                self._city_reader = geoip2.database.Reader(GEOIP_CITY_PATH)
                logger.info("✅ GeoLite2-City database loaded")

            if os.path.exists(GEOIP_ASN_PATH):
                self._asn_reader = geoip2.database.Reader(GEOIP_ASN_PATH)
                logger.info("✅ GeoLite2-ASN database loaded")

            self._loaded = True
        except Exception as e:
            logger.warning(f"GeoIP databases not available: {e}")
            logger.warning("Run: bash scripts/download-geoip.sh")

    def lookup(self, ip: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Look up country code and ASN for an IP address.
        Returns (country_iso, asn_org) tuple.
        """
        if not self._loaded:
            return None, None

        country = None
        asn = None

        try:
            if self._city_reader:
                resp = self._city_reader.city(ip)
                country = resp.country.iso_code
        except Exception:
            pass

        try:
            if self._asn_reader:
                resp = self._asn_reader.asn(ip)
                asn = resp.autonomous_system_organization
        except Exception:
            pass

        return country, asn

    def close(self):
        """Close GeoIP database readers."""
        if self._city_reader:
            self._city_reader.close()
        if self._asn_reader:
            self._asn_reader.close()
