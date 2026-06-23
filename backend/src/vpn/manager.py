"""
NetWatch AI — WireGuard Manager
Python wrapper for `wg` CLI and encryption utilities.
Falls back to pure-Python key generation when `wg` CLI is unavailable.
"""

import subprocess
import logging
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from src.core.config import settings

logger = logging.getLogger("netwatch.vpn.manager")

# Initialize Fernet cipher suite for private key encryption
cipher = Fernet(settings.VPN_ENCRYPTION_KEY.encode())

def _wg_available() -> bool:
    """Check if the `wg` CLI tool is available."""
    try:
        subprocess.run(["wg", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

WG_CLI_AVAILABLE = _wg_available()

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

def _generate_keys_python() -> tuple[str, str, str]:
    """Generate WireGuard keys using pure Python (cryptography library)."""
    # Generate private key
    private_key_obj = X25519PrivateKey.generate()
    private_key_bytes = private_key_obj.private_bytes_raw()
    private_key = base64.b64encode(private_key_bytes).decode()

    # Generate public key from private key
    public_key_bytes = private_key_obj.public_key().public_bytes_raw()
    public_key = base64.b64encode(public_key_bytes).decode()

    # Generate preshared key (32 random bytes, base64 encoded)
    preshared_key = base64.b64encode(os.urandom(32)).decode()

    return private_key, public_key, preshared_key

def _generate_keys_cli() -> tuple[str, str, str]:
    """Generate WireGuard keys using the `wg` CLI tool."""
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

def generate_keys() -> tuple[str, str, str]:
    """
    Generate WireGuard private, public, and preshared keys.
    Uses `wg` CLI if available, otherwise falls back to pure Python.
    Returns:
        (private_key, public_key, preshared_key)
    """
    if WG_CLI_AVAILABLE:
        try:
            return _generate_keys_cli()
        except subprocess.CalledProcessError as e:
            logger.warning(f"wg CLI key generation failed, falling back to Python: {e.stderr}")
    
    logger.info("Using pure-Python key generation (wg CLI not available)")
    return _generate_keys_python()

def sync_wireguard_config(config_path: str):
    """
    Applies the given WireGuard config to the interface wg0 dynamically.
    Uses `wg syncconf wg0 <(wg-quick strip config_path)`.
    Gracefully skips if WireGuard is not installed.
    """
    if not WG_CLI_AVAILABLE:
        logger.info("WireGuard CLI not available — skipping config sync (development mode)")
        return

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
    if not WG_CLI_AVAILABLE:
        return {}

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
