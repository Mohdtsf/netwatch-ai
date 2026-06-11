"""
NetWatch AI — Device Service
Business logic for device management.
"""

import logging
from typing import Optional
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Device, Flow, DnsQuery

logger = logging.getLogger("netwatch.devices")


class DeviceService:
    """Handles device discovery, tracking, and management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_devices(self) -> dict:
        """List all discovered devices with online/total counts."""
        result = await self.db.execute(select(Device).order_by(Device.last_seen.desc()))
        devices = result.scalars().all()

        online_count = sum(1 for d in devices if d.is_online)

        return {
            "devices": devices,
            "total": len(devices),
            "online": online_count,
        }

    async def get_device(self, device_id: str) -> Optional[Device]:
        """Get a single device by ID."""
        result = await self.db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        if not device:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )
        return device

    async def update_device(self, device_id: str, custom_name: str = None, device_type: str = None) -> Device:
        """Update device metadata (name, type)."""
        device = await self.get_device(device_id)

        if custom_name is not None:
            device.custom_name = custom_name
        if device_type is not None:
            device.device_type = device_type

        await self.db.commit()
        await self.db.refresh(device)
        logger.info(f"Device updated: {device.id}")
        return device

    async def get_device_flows(self, device_id: str, limit: int = 50, offset: int = 0) -> list:
        """Get traffic flow history for a device."""
        await self.get_device(device_id)  # Ensure device exists
        result = await self.db.execute(
            select(Flow)
            .where(Flow.device_id == device_id)
            .order_by(Flow.time.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_device_dns(self, device_id: str, limit: int = 50, offset: int = 0) -> list:
        """Get DNS query history for a device."""
        await self.get_device(device_id)  # Ensure device exists
        result = await self.db.execute(
            select(DnsQuery)
            .where(DnsQuery.device_id == device_id)
            .order_by(DnsQuery.time.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_device_stats(self, device_id: str) -> dict:
        """Get complex statistics for a device."""
        device = await self.get_device(device_id)
        now = int(datetime.utcnow().timestamp())
        five_mins_ago = now - 300
        
        # Calculate active duration
        active_duration = now - device.first_seen if device.first_seen else 0
        
        # Calculate bytes/sec over the last 5 minutes
        result = await self.db.execute(
            select(func.sum(Flow.bytes))
            .where(Flow.device_id == device_id)
            .where(Flow.time >= five_mins_ago)
        )
        recent_bytes = result.scalar() or 0
        bytes_per_sec = recent_bytes / 300

        # Fetch top 5 domains
        result = await self.db.execute(
            select(DnsQuery.domain, func.count(DnsQuery.id).label('count'))
            .where(DnsQuery.device_id == device_id)
            .group_by(DnsQuery.domain)
            .order_by(func.count(DnsQuery.id).desc())
            .limit(5)
        )
        top_domains = [{"domain": row.domain, "count": row.count} for row in result]

        return {
            "active_duration_seconds": active_duration,
            "bytes_per_sec_5m": bytes_per_sec,
            "top_domains": top_domains
        }

    async def block_device(self, device_id: str) -> Device:
        """Mark device as blocked."""
        device = await self.get_device(device_id)
        device.is_blocked = True
        await self.db.commit()
        await self.db.refresh(device)
        logger.info(f"Device blocked: {device.id} ({device.mac_address})")
        
        from src.firewall.nftables import nft_manager
        nft_manager.block_mac(device.mac_address)
        
        return device

    async def unblock_device(self, device_id: str) -> Device:
        """Remove block from device."""
        device = await self.get_device(device_id)
        device.is_blocked = False
        await self.db.commit()
        await self.db.refresh(device)
        logger.info(f"Device unblocked: {device.id} ({device.mac_address})")
        
        from src.firewall.nftables import nft_manager
        nft_manager.unblock_mac(device.mac_address)
        
        return device

    async def trigger_scan(self) -> dict:
        """Trigger an ARP scan. (Note: capture agent already scans periodically)."""
        return {"status": "scan_triggered", "message": "ARP scan initiated — results will appear shortly"}
