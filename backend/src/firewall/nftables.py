import logging
import subprocess

logger = logging.getLogger("netwatch.firewall.nftables")

class NftablesManager:
    """
    Manages nftables rules for Phase 6 Packet Firewall using dynamic sets.
    Requires NET_ADMIN capabilities.
    """
    def __init__(self, table_name: str = "netwatch"):
        self.table_name = table_name

    def _run_cmd(self, cmd: list) -> bool:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"nftables command failed: {' '.join(cmd)}")
            logger.error(f"Error output: {e.stderr}")
            return False

    def block_ip(self, ip_address: str) -> bool:
        """Add an IP address to the blocked_ips set."""
        cmd = ["nft", "add", "element", "inet", self.table_name, "blocked_ips", "{", ip_address, "}"]
        success = self._run_cmd(cmd)
        if success:
            logger.info(f"Successfully added IP {ip_address} to blocked_ips")
        return success

    def unblock_ip(self, ip_address: str) -> bool:
        """Remove an IP address from the blocked_ips set."""
        cmd = ["nft", "delete", "element", "inet", self.table_name, "blocked_ips", "{", ip_address, "}"]
        success = self._run_cmd(cmd)
        if success:
            logger.info(f"Successfully removed IP {ip_address} from blocked_ips")
        return success

    def block_mac(self, mac_address: str) -> bool:
        """Add a MAC address to the blocked_macs set."""
        cmd = ["nft", "add", "element", "inet", self.table_name, "blocked_macs", "{", mac_address, "}"]
        success = self._run_cmd(cmd)
        if success:
            logger.info(f"Successfully added MAC {mac_address} to blocked_macs")
        return success

    def unblock_mac(self, mac_address: str) -> bool:
        """Remove a MAC address from the blocked_macs set."""
        cmd = ["nft", "delete", "element", "inet", self.table_name, "blocked_macs", "{", mac_address, "}"]
        success = self._run_cmd(cmd)
        if success:
            logger.info(f"Successfully removed MAC {mac_address} from blocked_macs")
        return success

    def block_port(self, port: str) -> bool:
        """Add a port to the blocked_ports set."""
        cmd = ["nft", "add", "element", "inet", self.table_name, "blocked_ports", "{", str(port), "}"]
        success = self._run_cmd(cmd)
        if success:
            logger.info(f"Successfully added port {port} to blocked_ports")
        return success

    def unblock_port(self, port: str) -> bool:
        """Remove a port from the blocked_ports set."""
        cmd = ["nft", "delete", "element", "inet", self.table_name, "blocked_ports", "{", str(port), "}"]
        success = self._run_cmd(cmd)
        if success:
            logger.info(f"Successfully removed port {port} from blocked_ports")
        return success

    def set_rate_limit(self, ip_address: str) -> bool:
        """Add an IP address to the rate_limited set."""
        cmd = ["nft", "add", "element", "inet", self.table_name, "rate_limited", "{", ip_address, "}"]
        success = self._run_cmd(cmd)
        if success:
            logger.info(f"Successfully added IP {ip_address} to rate_limited")
        return success

    def remove_rate_limit(self, ip_address: str) -> bool:
        """Remove an IP address from the rate_limited set."""
        cmd = ["nft", "delete", "element", "inet", self.table_name, "rate_limited", "{", ip_address, "}"]
        success = self._run_cmd(cmd)
        if success:
            logger.info(f"Successfully removed IP {ip_address} from rate_limited")
        return success

nft_manager = NftablesManager()
