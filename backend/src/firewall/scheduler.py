import logging
import time
from sqlalchemy import select
from src.core.database import async_session
from src.core.models import FirewallRule
from src.firewall.service import FirewallService

logger = logging.getLogger("netwatch.firewall.scheduler")

async def cleanup_expired_firewall_rules():
    """Remove firewall rules that have expired."""
    now = int(time.time())
    
    async with async_session() as db:
        # Find all rules that have expired
        result = await db.execute(
            select(FirewallRule).where(
                FirewallRule.expires_at != None,
                FirewallRule.expires_at <= now
            )
        )
        expired_rules = result.scalars().all()
        
        for rule in expired_rules:
            logger.info(f"Removing expired firewall rule: {rule.rule_type} {rule.target}")
            await FirewallService.delete_rule(db, rule.id)
