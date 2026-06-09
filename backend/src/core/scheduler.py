"""
NetWatch AI — APScheduler Setup
Background task scheduler that runs inside the FastAPI process.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger("netwatch.scheduler")

scheduler = AsyncIOScheduler()


async def start_scheduler():
    """Initialize and start the background task scheduler."""
    if scheduler.running:
        return

    # ── Register scheduled tasks ──────────────
    # These are placeholders — each phase adds its own jobs

    # Phase 3: ARP scan every 30 seconds
    # scheduler.add_job(arp_scan_task, IntervalTrigger(seconds=30), id="arp_scan")

    # Phase 5: Blocklist update daily
    # scheduler.add_job(update_blocklists, IntervalTrigger(hours=24), id="blocklist_update")

    # Phase 5: DNS log tailer every 5 seconds
    # scheduler.add_job(tail_dns_log, IntervalTrigger(seconds=5), id="dns_log_tailer")

    # Retention cleanup: daily
    # scheduler.add_job(cleanup_old_data, IntervalTrigger(hours=24), id="data_cleanup")

    scheduler.start()
    logger.info("✅ APScheduler started")


async def stop_scheduler():
    """Gracefully stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
