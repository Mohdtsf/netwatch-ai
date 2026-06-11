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
                logger.info(f"✅ MAC vendor database loaded from JSON ({len(self._vendors)} entries)")
                self._loaded = True
        except Exception as e:
            logger.warning(f"Error loading MAC vendors from JSON: {e}")

        # Fallback or additional load from CSV
        csv_path = os.getenv("MAC_VENDORS_CSV_PATH", "/home/tauseef/Tauseef/Programming/Projects/netwatch/data/oui.csv")
        # In case we are running inside docker or differently configured
        if not os.path.exists(csv_path):
            csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "oui.csv")
            
        if os.path.exists(csv_path):
            try:
                import csv
                count = 0
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        oui = row.get("Assignment", "").strip().upper()
                        org = row.get("Organization Name", "").strip()
                        if oui and org and oui not in self._vendors:
                            self._vendors[oui] = org
                            count += 1
                logger.info(f"✅ MAC vendor database loaded from CSV ({count} new entries)")
                self._loaded = True
            except Exception as e:
                logger.warning(f"Error loading MAC vendors from CSV: {e}")
                
        if not self._loaded:
            logger.info("No MAC vendor database found (JSON or CSV).")

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
