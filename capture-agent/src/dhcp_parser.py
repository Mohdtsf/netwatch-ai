"""
NetWatch AI — DHCP Lease Parser
Reads local DHCP leases to map MAC addresses to hostnames.
"""

import os
import re
import logging
from typing import Dict, Optional

logger = logging.getLogger("netwatch.capture.dhcp")

class DhcpParser:
    def __init__(self, lease_files: list[str] = None):
        self.lease_files = lease_files or [
            "/var/lib/misc/dnsmasq.leases",
            "/var/lib/dhcp/dhcpd.leases",
            "/var/lib/dhcpd/dhcpd.leases"
        ]

    def get_hostnames(self) -> Dict[str, str]:
        """
        Returns a dictionary mapping MAC addresses to hostnames.
        e.g., {"00:11:22:33:44:55": "my-laptop"}
        """
        hostnames = {}
        for file_path in self.lease_files:
            if not os.path.exists(file_path):
                continue
            
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                
                if "dnsmasq" in file_path.lower():
                    # Parse dnsmasq format
                    # format: timestamp mac ip hostname client-id
                    for line in content.splitlines():
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            mac = parts[1].lower()
                            hostname = parts[3]
                            if hostname != "*":
                                hostnames[mac] = hostname
                else:
                    # Parse dhcpd format
                    lease_blocks = content.split("lease ")
                    for block in lease_blocks[1:]:
                        mac_match = re.search(r"hardware ethernet ([a-fA-F0-9:]+);", block)
                        hostname_match = re.search(r'client-hostname "([^"]+)";', block)
                        
                        if mac_match and hostname_match:
                            mac = mac_match.group(1).lower()
                            hostname = hostname_match.group(1)
                            hostnames[mac] = hostname
                            
            except Exception as e:
                logger.error(f"Failed to read DHCP leases from {file_path}: {e}")
                
        return hostnames
