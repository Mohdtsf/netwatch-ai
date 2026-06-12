"""
NetWatch AI — VPN Scheduler
Polls WireGuard interface to update peer status.
"""

import logging
from sqlalchemy.future import select
from src.core.database import async_session
from src.core.models import VpnPeer
from src.vpn.manager import get_wireguard_status

logger = logging.getLogger("netwatch.vpn.scheduler")

async def poll_vpn_status():
    """Poll WireGuard interface for peer stats and update DB."""
    try:
        status = get_wireguard_status()
        if not status:
            return
            
        async with async_session() as db:
            stmt = select(VpnPeer).where(VpnPeer.enabled == True)
            result = await db.execute(stmt)
            peers = result.scalars().all()
            
            for peer in peers:
                if peer.public_key in status:
                    info = status[peer.public_key]
                    peer.last_handshake = info["latest_handshake"]
                    peer.rx_bytes = info["transfer_rx"]
                    peer.tx_bytes = info["transfer_tx"]
                    if info["endpoint"]:
                        peer.endpoint = info["endpoint"]
            
            await db.commit()
    except Exception as e:
        logger.error(f"Error polling VPN status: {e}")
