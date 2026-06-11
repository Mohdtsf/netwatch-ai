import logging
import subprocess

logger = logging.getLogger("netwatch.firewall.nftables")

class NftablesManager:
    """
    Manages nftables rules for MAC-based blocking.
    Requires NET_ADMIN capabilities.
    """
    def __init__(self, table_name: str = "netwatch"):
        self.table_name = table_name
        self._ensure_table_exists()

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

    def _ensure_table_exists(self):
        """Ensure the netwatch table and chain exist in nftables."""
        # Add table
        self._run_cmd(["nft", "add", "table", "bridge", self.table_name])
        # Add base chain for MAC filtering
        self._run_cmd(["nft", "add", "chain", "bridge", self.table_name, "mac_filter", "{ type filter hook prerouting priority -200; policy accept; }"])
        
        # Add ip/ip6 table for NAT and L3 filtering
        self._run_cmd(["nft", "add", "table", "ip", self.table_name])
        self._run_cmd(["nft", "add", "chain", "ip", self.table_name, "prerouting", "{ type nat hook prerouting priority -100; policy accept; }"])
        self._run_cmd(["nft", "add", "chain", "ip", self.table_name, "forward", "{ type filter hook forward priority 0; policy accept; }"])
        
        logger.debug("Ensured nftables netwatch table and chains exist")

    def enable_dns_redirection(self):
        """Redirect all port 53 traffic to the local CoreDNS listener."""
        # Check if already exists or just add (nftables allows duplicate additions if not exact same, but we can flush or just add)
        # We will redirect DNS to 127.0.0.1:53 if it's on the host, but actually just intercept it.
        # nft add rule ip netwatch prerouting udp dport 53 redirect to :53
        # nft add rule ip netwatch prerouting tcp dport 53 redirect to :53
        
        udp_cmd = ["nft", "add", "rule", "ip", self.table_name, "prerouting", "udp", "dport", "53", "redirect", "to", ":53"]
        tcp_cmd = ["nft", "add", "rule", "ip", self.table_name, "prerouting", "tcp", "dport", "53", "redirect", "to", ":53"]
        
        self._run_cmd(udp_cmd)
        self._run_cmd(tcp_cmd)
        logger.info("Enabled DNS redirection (DNAT) to local CoreDNS listener")

    def block_dot(self):
        """Block DoT (DNS over TLS) on port 853 to prevent evasion."""
        # nft add rule ip netwatch forward tcp dport 853 drop
        # nft add rule ip netwatch forward udp dport 853 drop
        udp_cmd = ["nft", "add", "rule", "ip", self.table_name, "forward", "udp", "dport", "853", "drop"]
        tcp_cmd = ["nft", "add", "rule", "ip", self.table_name, "forward", "tcp", "dport", "853", "drop"]
        
        self._run_cmd(udp_cmd)
        self._run_cmd(tcp_cmd)
        logger.info("Enabled DoT (Port 853) blocking")

    def block_mac(self, mac_address: str) -> bool:
        """Add a rule to drop all traffic from a specific MAC address."""
        # e.g., nft add rule bridge netwatch mac_filter ether saddr 00:11:22:33:44:55 drop
        cmd = [
            "nft", "add", "rule", "bridge", self.table_name, "mac_filter",
            "ether", "saddr", mac_address, "drop"
        ]
        success = self._run_cmd(cmd)
        if success:
            logger.info(f"Successfully added nftables block rule for MAC: {mac_address}")
        return success

    def unblock_mac(self, mac_address: str) -> bool:
        """Remove the drop rule for a specific MAC address."""
        # To delete by handle we would need to parse `nft -a list ruleset`,
        # but for simple rules we can delete by rule definition if supported by the nft version.
        # Alternatively, find the handle:
        find_cmd = ["nft", "-a", "list", "chain", "bridge", self.table_name, "mac_filter"]
        try:
            result = subprocess.run(find_cmd, capture_output=True, text=True, check=True)
            handle = None
            for line in result.stdout.splitlines():
                if mac_address in line.lower() and "drop" in line:
                    # extract handle ID
                    parts = line.split("handle")
                    if len(parts) > 1:
                        handle = parts[1].strip()
                        break
            
            if handle:
                del_cmd = ["nft", "delete", "rule", "bridge", self.table_name, "mac_filter", "handle", handle]
                success = self._run_cmd(del_cmd)
                if success:
                    logger.info(f"Successfully removed nftables block rule for MAC: {mac_address}")
                return success
            else:
                logger.warning(f"Could not find nftables block rule for MAC: {mac_address} to unblock")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list nftables rules to find handle: {e}")
            return False

nft_manager = NftablesManager()
