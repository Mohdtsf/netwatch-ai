"""
NetWatch AI — MAC Vendor Lookup
Maps MAC addresses to device manufacturers using an OUI database.
"""

import logging
import json
import os
import urllib.request

logger = logging.getLogger("netwatch.capture.mac")

OUI_URL = "https://raw.githubusercontent.com/tauseef/netwatch-ai/main/data/mac-vendors.json" # Just an example, let's download a real one or handle missing gracefully.
MAC_VENDORS_PATH = os.getenv("MAC_VENDORS_PATH", "/app/data/mac-vendors.json")

class MacVendorLookup:
    """
    Looks up MAC addresses to find the device manufacturer.
    """

    def __init__(self):
        self._vendors: dict[str, str] = {}
        self._loaded = False

    def load(self):
        """Load MAC vendors database."""
        if not os.path.exists(MAC_VENDORS_PATH):
            logger.info("mac-vendors.json not found, attempting to download...")
            try:
                # Basic public list download if needed. We'll use macaddress.io or similar if available, 
                # but for now we'll just handle an empty list.
                # In real scenario, user would run download script.
                pass
            except Exception as e:
                logger.warning(f"Could not download MAC vendors: {e}")
        
        try:
            if os.path.exists(MAC_VENDORS_PATH):
                with open(MAC_VENDORS_PATH, "r") as f:
                    self._vendors = json.load(f)
                logger.info(f"✅ MAC vendor database loaded ({len(self._vendors)} entries)")
                self._loaded = True
        except Exception as e:
            logger.warning(f"Error loading MAC vendors: {e}")

    def lookup(self, mac: str) -> str | None:
        """
        Look up the vendor for a given MAC address.
        MAC should be in format XX:XX:XX:XX:XX:XX or XXXXXX...
        """
        if not self._loaded or not mac:
            return None
        
        # Extract OUI (first 3 bytes)
        clean_mac = mac.replace(":", "").upper()
        if len(clean_mac) >= 6:
            oui = clean_mac[:6]
            return self._vendors.get(oui)
        return None
