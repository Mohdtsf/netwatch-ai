"""
NetWatch AI — APScheduler Setup
Background task scheduler with real jobs that runs inside the FastAPI process.
"""

import logging
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import delete

from src.core.config import settings

logger = logging.getLogger("netwatch.scheduler")

scheduler = AsyncIOScheduler()


# ── Scheduled Jobs ────────────────────────────


async def cleanup_old_data():
    """Delete data older than configured retention period."""
    from src.core.database import async_session
    from src.core.models import DnsQuery, Flow

    async with async_session() as db:
        now = int(time.time())
        cutoff_flows = now - (settings.FLOW_RETENTION_DAYS * 86400)
        cutoff_dns = now - (settings.DNS_RETENTION_DAYS * 86400)

        flow_result = await db.execute(delete(Flow).where(Flow.time < cutoff_flows))
        dns_result = await db.execute(delete(DnsQuery).where(DnsQuery.time < cutoff_dns))
        await db.commit()

        flow_deleted = flow_result.rowcount
        dns_deleted = dns_result.rowcount

        if flow_deleted or dns_deleted:
            logger.info(
                f"🗑️  Data cleanup: {flow_deleted} flows, {dns_deleted} DNS queries removed "
                f"(retention: flows={settings.FLOW_RETENTION_DAYS}d, dns={settings.DNS_RETENTION_DAYS}d)"
            )


async def health_ping():
    """Log service health status periodically."""
    logger.debug("💓 Health ping — scheduler alive")


async def admin_user_check():
    """Create the initial admin user from env vars if no users exist."""
    from src.auth.service import AuthService
    from src.core.database import async_session

    async with async_session() as db:
        service = AuthService(db=db)
        await service.create_initial_admin()

async def blocklist_update_job():
    """Daily job to update DNS blocklists."""
    from src.dns.blocklist_updater import update_blocklists
    await update_blocklists()


# ── Scheduler Lifecycle ────────────────────────


async def start_scheduler():
    """Initialize and start the background task scheduler with all jobs registered."""
    if scheduler.running:
        return

    # Data cleanup — runs daily at 3:00 AM
    scheduler.add_job(
        cleanup_old_data,
        CronTrigger(hour=3, minute=0),
        id="data_cleanup",
        name="Delete old flows/DNS data",
        replace_existing=True,
    )

    # Health ping — every 60 seconds
    scheduler.add_job(
        health_ping,
        IntervalTrigger(seconds=60),
        id="health_ping",
        name="Service health heartbeat",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("✅ APScheduler started with 2 jobs registered")

    # Run admin user check once on startup (not recurring)
    await admin_user_check()

    # Start DNS blocklist updater job (runs daily at 4:00 AM)
    scheduler.add_job(
        blocklist_update_job,
        CronTrigger(hour=4, minute=0),
        id="blocklist_update",
        name="Update DNS blocklists",
        replace_existing=True,
    )

    # Start the continuous DNS log tailer as a background asyncio task
    from src.dns.log_tailer import tail_dns_logs
    import asyncio
    asyncio.create_task(tail_dns_logs())

    # Firewall cleanup job (runs every minute)
    from src.firewall.scheduler import cleanup_expired_firewall_rules
    scheduler.add_job(
        cleanup_expired_firewall_rules,
        IntervalTrigger(minutes=1),
        id="firewall_rule_cleanup",
        name="Clean up expired firewall rules",
        replace_existing=True,
    )


async def stop_scheduler():
    """Gracefully stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
