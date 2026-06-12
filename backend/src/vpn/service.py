"""
NetWatch AI — VPN Service
Generates WireGuard configuration and manages peers.
"""

import os
import base64
import qrcode
import subprocess
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.models import VpnPeer, Device
from src.core.config import settings
from src.vpn.manager import decrypt_key, sync_wireguard_config, generate_keys, encrypt_key

WG_CONF_PATH = "/etc/wireguard/wg0.conf"

async def generate_server_config(db: AsyncSession) -> str:
    """Generate the full wg0.conf server configuration string."""
    
    # Server config section
    server_priv_key_path = "/etc/wireguard/server_private.key"
    if not os.path.exists(server_priv_key_path):
        os.makedirs(os.path.dirname(server_priv_key_path), exist_ok=True)
        priv_proc = subprocess.run(["wg", "genkey"], capture_output=True, text=True, check=True)
        with open(server_priv_key_path, "w") as f:
            f.write(priv_proc.stdout.strip())
            
    with open(server_priv_key_path, "r") as f:
        server_private_key = f.read().strip()
        
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
    """Write config to disk and sync with interface."""
    config_str = await generate_server_config(db)
    
    os.makedirs(os.path.dirname(WG_CONF_PATH), exist_ok=True)
    with open(WG_CONF_PATH, "w") as f:
        f.write(config_str)
        
    sync_wireguard_config(WG_CONF_PATH)

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
        endpoint = "<SERVER_PUBLIC_IP>"
        
    config.append(f"Endpoint = {endpoint}:{settings.WG_SERVER_PORT}")
    config.append(f"AllowedIPs = {allowed_ips}")
    config.append("PersistentKeepalive = 25")
    
    return "\n".join(config)

def generate_qr_code(config_str: str) -> str:
    """Generate a base64 encoded PNG QR code for the given config."""
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
    return f"data:image/png;base64,{img_str}"

async def get_server_public_key() -> str:
    """Retrieve the server's public key."""
    server_priv_key_path = "/etc/wireguard/server_private.key"
    if not os.path.exists(server_priv_key_path):
        return ""
    with open(server_priv_key_path, "r") as f:
        priv_key = f.read().strip()
        
    proc = subprocess.run(["wg", "pubkey"], input=priv_key, capture_output=True, text=True, check=True)
    return proc.stdout.strip()

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
