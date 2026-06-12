"""
NetWatch AI — VPN Router
API endpoints for managing WireGuard VPN peers.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.database import get_db
from src.core.security import require_role
from src.core.models import VpnPeer
from src.vpn.service import (
    create_peer,
    generate_client_config,
    generate_qr_code,
    get_server_public_key,
    apply_server_config
)

router = APIRouter(prefix="/api/v1/vpn", tags=["vpn"])

class PeerCreate(BaseModel):
    peer_name: str
    device_id: Optional[str] = None
    tunnel_mode: str = "full"  # full | split

class PeerResponse(BaseModel):
    id: str
    peer_name: str
    device_id: Optional[str]
    public_key: str
    assigned_ip: str
    tunnel_mode: str
    enabled: bool
    last_handshake: Optional[int]
    rx_bytes: int
    tx_bytes: int
    
    class Config:
        from_attributes = True

@router.get("/peers", response_model=List[PeerResponse], dependencies=[Depends(require_role(["admin", "analyst", "viewer"]))])
async def list_peers(db: AsyncSession = Depends(get_db)):
    """List all VPN peers and their connection status."""
    stmt = select(VpnPeer).order_by(VpnPeer.created_at.desc())
    result = await db.execute(stmt)
    peers = result.scalars().all()
    return peers

@router.post("/peers", response_model=PeerResponse, dependencies=[Depends(require_role(["admin"]))])
async def add_peer(peer_in: PeerCreate, db: AsyncSession = Depends(get_db)):
    """Generate a new peer, returning the keys and config."""
    peer = await create_peer(db, peer_in.peer_name, peer_in.device_id, peer_in.tunnel_mode)
    return peer

@router.delete("/peers/{peer_id}", dependencies=[Depends(require_role(["admin"]))])
async def revoke_peer(peer_id: str, db: AsyncSession = Depends(get_db)):
    """Revoke a peer and hot-reload WireGuard configuration."""
    stmt = select(VpnPeer).where(VpnPeer.id == peer_id)
    result = await db.execute(stmt)
    peer = result.scalar_one_or_none()
    
    if not peer:
        raise HTTPException(status_code=404, detail="Peer not found")
        
    await db.delete(peer)
    await db.commit()
    
    await apply_server_config(db)
    
    return {"message": "Peer revoked successfully"}

@router.get("/peers/{peer_id}/qrcode", dependencies=[Depends(require_role(["admin", "analyst"]))])
async def get_peer_qrcode(peer_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve base64 QR code for a peer's configuration."""
    stmt = select(VpnPeer).where(VpnPeer.id == peer_id)
    result = await db.execute(stmt)
    peer = result.scalar_one_or_none()
    
    if not peer:
        raise HTTPException(status_code=404, detail="Peer not found")
        
    server_pub_key = await get_server_public_key()
    config_str = generate_client_config(peer, server_pub_key)
    qr_b64 = generate_qr_code(config_str)
    
    return {"qrcode": qr_b64}

@router.get("/peers/{peer_id}/config", response_class=PlainTextResponse, dependencies=[Depends(require_role(["admin", "analyst"]))])
async def get_peer_config(peer_id: str, db: AsyncSession = Depends(get_db)):
    """Download the raw .conf file for a peer."""
    stmt = select(VpnPeer).where(VpnPeer.id == peer_id)
    result = await db.execute(stmt)
    peer = result.scalar_one_or_none()
    
    if not peer:
        raise HTTPException(status_code=404, detail="Peer not found")
        
    server_pub_key = await get_server_public_key()
    config_str = generate_client_config(peer, server_pub_key)
    
    return config_str
