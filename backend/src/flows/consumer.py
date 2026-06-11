import asyncio
import json
import logging
from typing import List
from sqlalchemy import insert
from src.core.database import async_session
from src.core.models import Flow
from src.core.nats_client import nc, js
from src.core.websocket import broadcast_traffic

logger = logging.getLogger("netwatch.backend.consumer")

class FlowConsumer:
    """
    Consumes raw flows from NATS and writes them to SQLite in batches.
    """
    def __init__(self, batch_size: int = 100, flush_interval: float = 1.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._buffer: List[dict] = []
        self._running = False
        self._sub = None

    async def start(self):
        if not nc or not nc.is_connected:
            logger.warning("NATS not connected. Consumer not starting.")
            return

        self._running = True
        try:
            self._sub = await js.subscribe("netwatch.flows.raw", cb=self._message_handler)
            logger.info("✅ Flow consumer started on netwatch.flows.raw")
            asyncio.create_task(self._flush_loop())
        except Exception as e:
            logger.error(f"Failed to start flow consumer: {e}")

    async def stop(self):
        self._running = False
        if self._sub:
            await self._sub.unsubscribe()
        await self._flush()
        logger.info("Flow consumer stopped")

    async def _message_handler(self, msg):
        try:
            data = json.loads(msg.data.decode("utf-8"))
            self._buffer.append(data)
            
            # Broadcast to websocket live
            await broadcast_traffic(data)
            
            await msg.ack()
        except Exception as e:
            logger.error(f"Error processing NATS message: {e}")

    async def _flush_loop(self):
        while self._running:
            if len(self._buffer) >= self.batch_size:
                await self._flush()
            else:
                await asyncio.sleep(self.flush_interval)
                await self._flush()

    async def _flush(self):
        if not self._buffer:
            return

        batch = self._buffer[:]
        self._buffer.clear()

        try:
            from sqlalchemy.dialects.sqlite import insert as sqlite_insert
            from src.core.models import FlowAggregate

            async with async_session() as db:
                # Flow model doesn't have a duration column
                db_batch = []
                for b in batch:
                    f_dict = dict(b)
                    if "duration" in f_dict:
                        del f_dict["duration"]
                    db_batch.append(f_dict)
                    
                await db.execute(insert(Flow).values(db_batch))
                
                # Update flows_1min aggregates
                for flow in batch:
                    # round time down to minute
                    bucket = (flow["time"] // 60) * 60
                    stmt = sqlite_insert(FlowAggregate).values(
                        bucket=bucket,
                        src_ip=flow.get("src_ip", ""),
                        dst_ip=flow.get("dst_ip", ""),
                        total_bytes=flow.get("bytes", 0),
                        total_packets=flow.get("packets", 0)
                    ).on_conflict_do_update(
                        index_elements=["bucket", "src_ip", "dst_ip"],
                        set_={
                            "total_bytes": FlowAggregate.total_bytes + flow.get("bytes", 0),
                            "total_packets": FlowAggregate.total_packets + flow.get("packets", 0)
                        }
                    )
                    await db.execute(stmt)
                    
                await db.commit()
            logger.debug(f"Inserted batch of {len(batch)} flows into SQLite and updated aggregates")
        except Exception as e:
            logger.error(f"Failed to insert flows batch: {e}")
            # we don't re-add to buffer to avoid memory leak if DB is constantly failing, 
            # though in a robust system we might want some retry logic.

flow_consumer = FlowConsumer()
