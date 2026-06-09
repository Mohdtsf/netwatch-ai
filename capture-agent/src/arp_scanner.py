"""
NetWatch AI — ARP Network Scanner
Discovers devices on the local network using ARP requests.
"""

import logging
from typing import Optional

logger = logging.getLogger("netwatch.capture.arp")


class ArpScanner:
    """
    Discovers devices on the local network using ARP scanning.
    
    Sends ARP "who-has" requests to every IP in the subnet and
    collects responses to build a list of active devices with
    their MAC addresses.
    
    Also reads the system ARP cache for passively discovered devices.
    """

    def __init__(self, subnet: str = "192.168.1.0/24", interface: str = "eth0"):
        self.subnet = subnet
        self.interface = interface
        self._last_scan: list[dict] = []

    async def scan(self) -> list[dict]:
        """
        Perform an ARP scan of the subnet.
        
        Returns a list of dicts with: ip, mac, vendor
        TODO Phase 3: Implement with Scapy ARP.
        """
        logger.info(f"ARP scan stub: {self.subnet} on {self.interface}")
        return []

    def read_arp_cache(self) -> list[dict]:
        """
        Read the system ARP cache (/proc/net/arp on Linux).
        
        This is a zero-cost way to find recently-seen devices
        without sending any network traffic.
        """
        devices = []
        try:
            with open("/proc/net/arp", "r") as f:
                lines = f.readlines()[1:]  # skip header
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 6 and parts[3] != "00:00:00:00:00:00":
                        devices.append({
                            "ip": parts[0],
                            "mac": parts[3],
                            "interface": parts[5],
                        })
        except FileNotFoundError:
            logger.debug("ARP cache not available (not on Linux)")
        except Exception as e:
            logger.error(f"Error reading ARP cache: {e}")

        return devices

    @property
    def stats(self) -> dict:
        return {
            "subnet": self.subnet,
            "last_scan_count": len(self._last_scan),
        }
