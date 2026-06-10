"""
NetWatch AI — Device Service
Business logic for device management.
"""

import logging
from typing import Optional

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

    async def block_device(self, device_id: str) -> Device:
        """Mark device as blocked."""
        device = await self.get_device(device_id)
        device.is_blocked = True
        await self.db.commit()
        await self.db.refresh(device)
        logger.info(f"Device blocked: {device.id} ({device.mac_address})")
        # TODO Phase 6: add nftables MAC block rule
        return device

    async def unblock_device(self, device_id: str) -> Device:
        """Remove block from device."""
        device = await self.get_device(device_id)
        device.is_blocked = False
        await self.db.commit()
        await self.db.refresh(device)
        logger.info(f"Device unblocked: {device.id} ({device.mac_address})")
        # TODO Phase 6: remove nftables MAC block rule
        return device

    async def trigger_scan(self) -> dict:
        """Trigger an ARP scan (stub — implemented in Phase 3)."""
        # TODO Phase 3: integrate with capture-agent ARP scanner
        return {"status": "scan_triggered", "message": "ARP scan initiated — results will appear shortly"}
