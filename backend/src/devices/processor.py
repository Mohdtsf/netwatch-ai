import asyncio
import json
import logging
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from src.core.database import async_session
from src.core.models import Device, Alert
from src.core.nats_client import nc, js
from src.core.websocket import broadcast_device

logger = logging.getLogger("netwatch.backend.devices_processor")

class DeviceProcessor:
    def __init__(self):
        self._running = False
        self._sub = None

    async def start(self):
        if not nc or not nc.is_connected:
            logger.warning("NATS not connected. Device processor not starting.")
            return

        self._running = True
        try:
            self._sub = await js.subscribe("netwatch.devices.events", cb=self._message_handler)
            logger.info("✅ Device processor started on netwatch.devices.events")
        except Exception as e:
            logger.error(f"Failed to start device processor: {e}")

    async def stop(self):
        self._running = False
        if self._sub:
            await self._sub.unsubscribe()
        logger.info("Device processor stopped")

    async def _message_handler(self, msg):
        try:
            data = json.loads(msg.data.decode("utf-8"))
            await self._process_device(data)
            await msg.ack()
        except Exception as e:
            logger.error(f"Error processing device event: {e}")

    async def _process_device(self, data: dict):
        mac = data.get("mac")
        if not mac:
            return

        ip = data.get("ip")
        vendor = data.get("vendor", "Unknown")
        hostname = data.get("hostname", "Unknown")
        now = int(datetime.utcnow().timestamp())

        async with async_session() as db:
            # Check if device exists
            stmt = select(Device).where(Device.mac_address == mac)
            result = await db.execute(stmt)
            device = result.scalar_one_or_none()

            is_new = False
            if not device:
                is_new = True
                # Insert new device
                new_device = Device(
                    mac_address=mac,
                    ip_address=ip,
                    hostname=hostname if hostname else "Unknown",
                    vendor=vendor if vendor else "Unknown",
                    first_seen=now,
                    last_seen=now,
                    is_online=True
                )
                db.add(new_device)
                await db.commit()
                await db.refresh(new_device)

                # Generate alert
                alert = Alert(
                    severity="low",
                    type="NewDevice",
                    message=f"New device joined network: {hostname} ({mac}) - {vendor}",
                    source_ip=ip,
                    device_id=new_device.id
                )
                db.add(alert)
                await db.commit()
                
                logger.info(f"New device discovered: {mac} ({ip})")
                
                # Broadcast new device
                await broadcast_device({
                    "event": "new_device",
                    "device": {
                        "id": new_device.id,
                        "mac": mac,
                        "ip": ip,
                        "hostname": hostname,
                        "vendor": vendor,
                        "is_online": True,
                        "first_seen": new_device.first_seen,
                        "last_seen": new_device.last_seen
                    }
                })
            else:
                # Update existing device
                device.ip_address = ip
                device.last_seen = now
                if hostname and hostname != "Unknown" and device.hostname == "Unknown":
                    device.hostname = hostname
                if vendor and vendor != "Unknown" and device.vendor == "Unknown":
                    device.vendor = vendor
                    
                was_offline = not device.is_online
                device.is_online = True
                
                await db.commit()
                
                if was_offline:
                    await broadcast_device({
                        "event": "device_online",
                        "device_id": device.id,
                        "mac": mac,
                        "ip": ip
                    })

device_processor = DeviceProcessor()
