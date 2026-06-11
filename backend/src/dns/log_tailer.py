"""
NetWatch AI — DNS Log Tailer
Reads CoreDNS query logs, maps IPs to devices, and saves to SQLite.
"""

import logging
import asyncio
import os
import time
from datetime import datetime

logger = logging.getLogger("netwatch.dns.tailer")

LOG_FILE = "/app/coredns/dns-queries.log"

async def tail_dns_logs():
    """
    Tails the DNS query log file asynchronously.
    For production, this is a continuous async task started on boot.
    """
    from src.core.database import async_session
    from src.core.models import DnsQuery, Device
    from sqlalchemy import select
    from src.core.nats_client import nc
    import json
    
    if not os.path.exists(LOG_FILE):
        # Create empty if not exists to avoid errors
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        open(LOG_FILE, 'a').close()
        
    logger.info(f"Tailing DNS log file: {LOG_FILE}")
    
    # Open file and go to end
    file = open(LOG_FILE, 'r')
    file.seek(0, 2)
    
    # In-memory device cache to avoid DB spam
    device_cache = {}
    
    while True:
        line = file.readline()
        if not line:
            await asyncio.sleep(0.5)
            continue
            
        line = line.strip()
        if not line:
            continue
            
        try:
            # Expected format: "192.168.1.50 A example.com. NOERROR"
            parts = line.split()
            if len(parts) >= 4:
                src_ip = parts[0].split(':')[0] # Remove port if present
                qtype = parts[1]
                domain = parts[2].rstrip('.')
                rcode = parts[3]
                
                # Check if blocked (0.0.0.0 or NXDOMAIN might indicate block list)
                action = 'blocked' if rcode == 'NXDOMAIN' or rcode == 'REFUSED' else 'allowed'
                
                # Find device ID
                device_id = device_cache.get(src_ip)
                if not device_id:
                    async with async_session() as db:
                        result = await db.execute(select(Device).where(Device.ip_address == src_ip))
                        device = result.scalar_one_or_none()
                        if device:
                            device_id = device.id
                            device_cache[src_ip] = device_id
                            
                # Save to database
                async with async_session() as db:
                    query_record = DnsQuery(
                        time=int(time.time()),
                        device_id=device_id,
                        src_ip=src_ip,
                        domain=domain,
                        action=action,
                        category="unknown"
                    )
                    db.add(query_record)
                    await db.commit()
                    
                # Broadcast via WebSocket (handled by NATS)
                if nc and nc.is_connected:
                    msg = {
                        "time": int(time.time()),
                        "src_ip": src_ip,
                        "device_id": device_id,
                        "domain": domain,
                        "action": action,
                        "qtype": qtype,
                        "rcode": rcode
                    }
                    from src.core.websocket import broadcast_dns
                    await broadcast_dns(msg)
                    
        except Exception as e:
            logger.error(f"Error parsing DNS log line '{line}': {e}")
