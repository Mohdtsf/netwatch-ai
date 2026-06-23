"""
NetWatch AI — VPN Service
Generates WireGuard configuration and manages peers.
Falls back gracefully when WireGuard CLI/interface is unavailable (dev mode).
"""

import os
import base64
import logging
import subprocess
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

try:
    import qrcode
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

from src.core.models import VpnPeer, Device
from src.core.config import settings
from src.vpn.manager import decrypt_key, sync_wireguard_config, generate_keys, encrypt_key, WG_CLI_AVAILABLE

logger = logging.getLogger("netwatch.vpn.service")

WG_CONF_PATH = "/etc/wireguard/wg0.conf"

# Use a local fallback path for dev environments without /etc/wireguard access
_DATA_DIR = os.environ.get("WG_DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data", "wireguard"))
_SERVER_KEY_PATH = os.path.join(_DATA_DIR, "server_private.key")

def _ensure_server_key() -> str:
    """Ensure a server private key exists. Returns the private key string."""
    # Try the canonical /etc/wireguard path first (Docker/production)
    etc_key_path = "/etc/wireguard/server_private.key"
    if os.path.exists(etc_key_path):
        with open(etc_key_path, "r") as f:
            return f.read().strip()
    
    # Fall back to local data directory (development)
    if os.path.exists(_SERVER_KEY_PATH):
        with open(_SERVER_KEY_PATH, "r") as f:
            return f.read().strip()
    
    # Generate new server key
    priv_key, _, _ = generate_keys()
    
    # Try to write to /etc/wireguard first, then fallback
    for path in [etc_key_path, _SERVER_KEY_PATH]:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(priv_key)
            logger.info(f"Server private key generated and saved to {path}")
            return priv_key
        except (PermissionError, OSError):
            continue
    
    # If we can't write anywhere, just return the key in memory
    logger.warning("Could not persist server private key to disk")
    return priv_key


async def generate_server_config(db: AsyncSession) -> str:
    """Generate the full wg0.conf server configuration string."""
    
    server_private_key = _ensure_server_key()
        
    config = [
        "[Interface]",
        f"PrivateKey = {server_private_key}",
        f"Address = {settings.WG_SERVER_ADDRESS}",
        f"ListenPort = {settings.WG_SERVER_PORT}",
        'PostUp = nft add rule ip nat POSTROUTING oifname "eth0" masquerade',
        'PostDown = nft delete rule ip nat POSTROUTING oifname "eth0" masquerade',
        ""
    ]
    
    # Fetch all enabled peers
    stmt = select(VpnPeer).where(VpnPeer.enabled == True)
    result = await db.execute(stmt)
    peers = result.scalars().all()
    
    for peer in peers:
        config.append("[Peer]")
        if peer.peer_name:
            config.append(f"# {peer.peer_name}")
        config.append(f"PublicKey = {peer.public_key}")
        if peer.preshared_key_enc:
            config.append(f"PresharedKey = {decrypt_key(peer.preshared_key_enc)}")
        if peer.assigned_ip:
            config.append(f"AllowedIPs = {peer.assigned_ip}/32")
        config.append("")
        
    return "\n".join(config)

async def apply_server_config(db: AsyncSession):
    """Write config to disk and sync with interface. Skips gracefully in dev mode."""
    try:
        config_str = await generate_server_config(db)
    except Exception as e:
        logger.warning(f"Could not generate server config: {e}")
        return
    
    # Try to write the config file
    for path in [WG_CONF_PATH, os.path.join(_DATA_DIR, "wg0.conf")]:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(config_str)
            logger.info(f"WireGuard config written to {path}")
            break
        except (PermissionError, OSError):
            continue
    
    # Sync the running interface (will skip if wg CLI unavailable)
    try:
        sync_wireguard_config(WG_CONF_PATH)
    except Exception as e:
        logger.warning(f"Could not sync WireGuard config (dev mode): {e}")

def generate_client_config(peer: VpnPeer, server_public_key: str) -> str:
    """Generate the client .conf string for a peer."""
    private_key = decrypt_key(peer.private_key_enc) if peer.private_key_enc else "<MISSING_PRIVATE_KEY>"
    preshared_key = decrypt_key(peer.preshared_key_enc) if peer.preshared_key_enc else ""
    
    # Calculate AllowedIPs based on tunnel mode
    if peer.tunnel_mode == "split":
        # Only route local network and VPN subnet
        allowed_ips = f"{settings.SCAN_SUBNET}, {settings.WG_SERVER_ADDRESS}"
    else:
        # Full tunnel
        allowed_ips = "0.0.0.0/0"
        
    config = [
        "[Interface]",
        f"PrivateKey = {private_key}",
        f"Address = {peer.assigned_ip}/32",
        "DNS = 10.8.0.1", # Point to CoreDNS via WireGuard
        "",
        "[Peer]",
        f"PublicKey = {server_public_key}",
    ]
    if preshared_key:
        config.append(f"PresharedKey = {preshared_key}")
        
    endpoint = settings.WG_ENDPOINT
    if endpoint == "auto":
        try:
            import urllib.request
            with urllib.request.urlopen("https://api.ipify.org", timeout=2) as response:
                endpoint = response.read().decode('utf-8').strip()
        except Exception:
            endpoint = "127.0.0.1"
        
    config.append(f"Endpoint = {endpoint}:{settings.WG_SERVER_PORT}")
    config.append(f"AllowedIPs = {allowed_ips}")
    config.append("PersistentKeepalive = 25")
    
    return "\n".join(config)

def generate_qr_code(config_str: str) -> str:
    """Generate a base64 encoded PNG QR code for the given config."""
    if not QR_AVAILABLE:
        logger.warning("qrcode library not installed, returning placeholder")
        return ""
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(config_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

async def get_server_public_key() -> str:
    """Retrieve the server's public key."""
    server_private_key = _ensure_server_key()
    if not server_private_key:
        return ""
    
    if WG_CLI_AVAILABLE:
        try:
            proc = subprocess.run(["wg", "pubkey"], input=server_private_key, capture_output=True, text=True, check=True)
            return proc.stdout.strip()
        except subprocess.CalledProcessError:
            pass
    
    # Pure Python fallback: derive public key from private key
    try:
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
        import base64 as b64
        priv_key_bytes = b64.b64decode(server_private_key)
        priv_key_obj = X25519PrivateKey.from_private_bytes(priv_key_bytes)
        pub_key_bytes = priv_key_obj.public_key().public_bytes_raw()
        return b64.b64encode(pub_key_bytes).decode()
    except Exception as e:
        logger.warning(f"Could not derive server public key: {e}")
        return ""

async def get_next_available_ip(db: AsyncSession) -> str:
    """Find the next available IP in the 10.8.0.x subnet."""
    stmt = select(VpnPeer.assigned_ip).where(VpnPeer.assigned_ip.isnot(None))
    result = await db.execute(stmt)
    used_ips = set(result.scalars().all())
    
    for i in range(2, 255):
        ip = f"10.8.0.{i}"
        if ip not in used_ips:
            return ip
    raise RuntimeError("No available IP addresses in VPN subnet")

async def create_peer(db: AsyncSession, peer_name: str, device_id: str = None, tunnel_mode: str = "full") -> VpnPeer:
    """Create a new VPN peer, generate keys, and apply config."""
    priv_key, pub_key, psk = generate_keys()
    
    assigned_ip = await get_next_available_ip(db)
    
    peer = VpnPeer(
        peer_name=peer_name,
        device_id=device_id,
        public_key=pub_key,
        private_key_enc=encrypt_key(priv_key),
        preshared_key_enc=encrypt_key(psk),
        assigned_ip=assigned_ip,
        tunnel_mode=tunnel_mode,
        allowed_ips=f"{assigned_ip}/32", # Only allow traffic from this IP on the server
    )
    
    db.add(peer)
    await db.commit()
    await db.refresh(peer)
    
    # Update device if linked
    if device_id:
        device_stmt = select(Device).where(Device.id == device_id)
        device_result = await db.execute(device_stmt)
        device = device_result.scalar_one_or_none()
        if device:
            device.vpn_enabled = True
            await db.commit()
            
    await apply_server_config(db)
    return peer
