import asyncio
import json
import logging
from datetime import datetime

from src.core.database import async_session
from src.core.models import Alert, Device
from src.core.nats_client import nc, js
from src.core.websocket import broadcast_alert
from src.firewall.service import FirewallService

logger = logging.getLogger("netwatch.alerts.processor")

class AlertConsumer:
    """
    Consumes alerts from NATS, saves to SQLite, and triggers auto-block via firewall if critical.
    """
    def __init__(self):
        self._running = False
        self._sub = None

    async def start(self):
        if not nc or not nc.is_connected:
            logger.warning("NATS not connected. Alert consumer not starting.")
            return

        self._running = True
        try:
            self._sub = await js.subscribe("netwatch.alerts", cb=self._message_handler)
            logger.info("✅ Alert consumer started on netwatch.alerts")
        except Exception as e:
            logger.error(f"Failed to start alert consumer: {e}")

    async def stop(self):
        self._running = False
        if self._sub:
            await self._sub.unsubscribe()
        logger.info("Alert consumer stopped")

    async def _message_handler(self, msg):
        try:
            data = json.loads(msg.data.decode("utf-8"))
            
            # Broadcast to websocket live
            await broadcast_alert(data)
            
            # Process in DB
            await self._process_alert(data)
            
            await msg.ack()
        except Exception as e:
            logger.error(f"Error processing NATS alert message: {e}")

    async def _process_alert(self, data: dict):
        severity = data.get("severity", "low")
        source_ip = data.get("source_ip")
        device_id = data.get("device_id")
        
        auto_blocked = False
        
        async with async_session() as db:
            # Auto-block logic for critical alerts
            if severity == "critical":
                if source_ip:
                    # Create an IP block rule
                    logger.warning(f"🚨 CRITICAL ALERT: Auto-blocking IP {source_ip}")
                    await FirewallService.create_rule(
                        db=db,
                        rule_type="ip",
                        target=source_ip,
                        device_id=device_id,
                        action="drop",
                        auto_block=True
                    )
                    auto_blocked = True
                elif device_id:
                    # Get device MAC and block it
                    from sqlalchemy import select
                    result = await db.execute(select(Device).where(Device.id == device_id))
                    device = result.scalar_one_or_none()
                    if device and device.mac_address:
                        logger.warning(f"🚨 CRITICAL ALERT: Auto-blocking MAC {device.mac_address} (Device {device_id})")
                        await FirewallService.create_rule(
                            db=db,
                            rule_type="mac",
                            target=device.mac_address,
                            device_id=device_id,
                            action="drop",
                            auto_block=True
                        )
                        auto_blocked = True

            # Save alert to DB
            alert = Alert(
                severity=severity,
                type=data.get("type", "Unknown"),
                message=data.get("message", ""),
                source_ip=source_ip,
                destination_ip=data.get("destination_ip"),
                device_id=device_id,
                auto_blocked=auto_blocked,
                time=int(data.get("time", datetime.utcnow().timestamp()))
            )
            db.add(alert)
            await db.commit()

alert_processor = AlertConsumer()
