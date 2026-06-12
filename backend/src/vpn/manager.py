"""
NetWatch AI — WireGuard Manager
Python wrapper for `wg` CLI and encryption utilities.
"""

import subprocess
import logging
from cryptography.fernet import Fernet
from src.core.config import settings

logger = logging.getLogger("netwatch.vpn.manager")

# Initialize Fernet cipher suite for private key encryption
cipher = Fernet(settings.VPN_ENCRYPTION_KEY.encode())

def encrypt_key(key: str) -> str:
    """Encrypt a WireGuard private key."""
    if not key:
        return ""
    return cipher.encrypt(key.encode()).decode()

def decrypt_key(encrypted_key: str) -> str:
    """Decrypt a WireGuard private key."""
    if not encrypted_key:
        return ""
    return cipher.decrypt(encrypted_key.encode()).decode()

def generate_keys() -> tuple[str, str, str]:
    """
    Generate WireGuard private, public, and preshared keys.
    Returns:
        (private_key, public_key, preshared_key)
    """
    try:
        # Generate private key
        priv_proc = subprocess.run(
            ["wg", "genkey"], capture_output=True, text=True, check=True
        )
        private_key = priv_proc.stdout.strip()

        # Generate public key from private key
        pub_proc = subprocess.run(
            ["wg", "pubkey"], input=private_key, capture_output=True, text=True, check=True
        )
        public_key = pub_proc.stdout.strip()

        # Generate preshared key
        psk_proc = subprocess.run(
            ["wg", "genpsk"], capture_output=True, text=True, check=True
        )
        preshared_key = psk_proc.stdout.strip()

        return private_key, public_key, preshared_key
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to generate WireGuard keys: {e.stderr}")
        raise RuntimeError("WireGuard key generation failed") from e

def sync_wireguard_config(config_path: str):
    """
    Applies the given WireGuard config to the interface wg0 dynamically.
    Uses `wg syncconf wg0 <(wg-quick strip config_path)`.
    """
    try:
        # First ensure the interface exists and is up
        subprocess.run(["ip", "link", "show", "wg0"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        # Interface doesn't exist, bring it up with wg-quick
        logger.info("wg0 interface not found, bringing it up...")
        try:
            subprocess.run(["wg-quick", "up", config_path], capture_output=True, text=True, check=True)
            return
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to bring up wg0: {e.stderr}")
            raise RuntimeError("Failed to start WireGuard interface") from e

    # Interface exists, sync configuration without dropping connections
    logger.info("wg0 interface exists, syncing configuration...")
    try:
        # We need to run `wg-quick strip` then pipe it to `wg syncconf`
        strip_proc = subprocess.run(["wg-quick", "strip", config_path], capture_output=True, text=True, check=True)
        stripped_config = strip_proc.stdout.encode()
        
        sync_proc = subprocess.Popen(["wg", "syncconf", "wg0", "/dev/stdin"], stdin=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        _, stderr = sync_proc.communicate(input=stripped_config.decode())
        if sync_proc.returncode != 0:
            logger.error(f"wg syncconf failed: {stderr}")
            raise RuntimeError(f"wg syncconf failed: {stderr}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to strip wg0 config: {e.stderr}")
        raise RuntimeError("Failed to sync WireGuard configuration") from e

def get_wireguard_status() -> dict:
    """
    Executes `wg show wg0 dump` and parses the output.
    Returns a dict mapping public keys to status info.
    """
    try:
        proc = subprocess.run(["wg", "show", "wg0", "dump"], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return {} # interface likely down

    lines = proc.stdout.strip().split("\n")
    if not lines or len(lines) < 2:
        return {}
    
    # First line is server info, subsequent lines are peers
    # Format: public_key preshared_key endpoint allowed_ips latest_handshake transfer_rx transfer_tx persistent_keepalive
    status = {}
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) >= 8:
            pubkey = parts[0]
            status[pubkey] = {
                "endpoint": parts[2] if parts[2] != "(none)" else None,
                "allowed_ips": parts[3],
                "latest_handshake": int(parts[4]),
                "transfer_rx": int(parts[5]),
                "transfer_tx": int(parts[6])
            }
    return status
