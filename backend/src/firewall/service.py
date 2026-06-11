from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import time

from src.core.models import FirewallRule, Device
from src.firewall.nftables import nft_manager

class FirewallService:
    @staticmethod
    async def get_rules(db: AsyncSession) -> List[FirewallRule]:
        result = await db.execute(select(FirewallRule))
        return list(result.scalars().all())

    @staticmethod
    async def create_rule(
        db: AsyncSession,
        rule_type: str,
        target: str,
        device_id: Optional[str] = None,
        direction: str = "both",
        action: str = "drop",
        schedule: Optional[str] = None,
        auto_block: bool = False,
        expires_at: Optional[int] = None
    ) -> FirewallRule:
        rule = FirewallRule(
            rule_type=rule_type,
            target=target,
            device_id=device_id,
            direction=direction,
            action=action,
            schedule=schedule,
            auto_block=auto_block,
            expires_at=expires_at,
            enabled=True
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)

        # Apply to nftables
        FirewallService._apply_rule(rule)

        return rule

    @staticmethod
    async def delete_rule(db: AsyncSession, rule_id: str) -> bool:
        result = await db.execute(select(FirewallRule).where(FirewallRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            return False

        # Remove from nftables
        FirewallService._remove_rule(rule)

        await db.delete(rule)
        await db.commit()
        return True

    @staticmethod
    def _apply_rule(rule: FirewallRule):
        if not rule.enabled:
            return
        
        if rule.rule_type == "ip":
            nft_manager.block_ip(rule.target)
        elif rule.rule_type == "mac":
            nft_manager.block_mac(rule.target)
        elif rule.rule_type == "port":
            nft_manager.block_port(rule.target)
        elif rule.rule_type == "rate_limit":
            nft_manager.set_rate_limit(rule.target)

    @staticmethod
    def _remove_rule(rule: FirewallRule):
        if rule.rule_type == "ip":
            nft_manager.unblock_ip(rule.target)
        elif rule.rule_type == "mac":
            nft_manager.unblock_mac(rule.target)
        elif rule.rule_type == "port":
            nft_manager.unblock_port(rule.target)
        elif rule.rule_type == "rate_limit":
            nft_manager.remove_rate_limit(rule.target)

    @staticmethod
    async def sync_all_rules(db: AsyncSession):
        """Restore all enabled firewall rules to nftables (e.g., on startup)."""
        result = await db.execute(select(FirewallRule).where(FirewallRule.enabled == True))
        rules = result.scalars().all()
        for rule in rules:
            FirewallService._apply_rule(rule)
