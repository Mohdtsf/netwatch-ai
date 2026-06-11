import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.models import DnsRule, User
from src.core.security import get_current_user
from src.dns.schemas import DnsRuleCreate, DnsRuleResponse, DnsQueryResponse
from src.dns.rule_manager import generate_device_rules
from src.dns.blocklist_updater import update_blocklists, load_config, AVAILABLE_LISTS, CONFIG_FILE
import json

logger = logging.getLogger("netwatch.dns.router")
router = APIRouter(prefix="/api/v1/dns", tags=["dns"])

@router.get("/rules", response_model=List[DnsRuleResponse])
async def list_dns_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all custom DNS rules."""
    result = await db.execute(select(DnsRule).order_by(DnsRule.created_at.desc()))
    return result.scalars().all()

@router.post("/rules", response_model=DnsRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_dns_rule(
    rule: DnsRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new DNS rule (block or allow a domain)."""
    if current_user.role == "viewer":
        raise HTTPException(status_code=403, detail="Not authorized to create rules")
        
    db_rule = DnsRule(
        device_id=rule.device_id,
        domain_pattern=rule.domain_pattern,
        action=rule.action,
        category=rule.category,
        created_by=current_user.id
    )
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    
    # Regenerate CoreDNS configuration
    await generate_device_rules()
    
    return db_rule

@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dns_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a DNS rule."""
    if current_user.role == "viewer":
        raise HTTPException(status_code=403, detail="Not authorized to delete rules")
        
    result = await db.execute(select(DnsRule).where(DnsRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    await db.delete(rule)
    await db.commit()
    
    # Regenerate CoreDNS configuration
    await generate_device_rules()

@router.post("/blocklist/update", status_code=status.HTTP_202_ACCEPTED)
async def trigger_blocklist_update(
    current_user: User = Depends(get_current_user),
):
    """Manually trigger blocklist update."""
    if current_user.role == "viewer":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # Run in background via asyncio
    import asyncio
    asyncio.create_task(update_blocklists())
    return {"message": "Blocklist update triggered"}

@router.get("/blocklist/config")
async def get_blocklist_config(
    current_user: User = Depends(get_current_user),
):
    """Get all available blocklist categories and current configuration."""
    config = load_config()
    return {
        "available_lists": AVAILABLE_LISTS,
        "config": config
    }

@router.post("/blocklist/config", status_code=status.HTTP_200_OK)
async def update_blocklist_config(
    new_config: dict,
    current_user: User = Depends(get_current_user),
):
    """Update blocklist configuration (requires admin/analyst)."""
    if current_user.role == "viewer":
        raise HTTPException(status_code=403, detail="Not authorized to edit configuration")
        
    # Validate structure
    if "enabled_lists" not in new_config:
        raise HTTPException(status_code=400, detail="Missing 'enabled_lists' key in config")
        
    # Write to file
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(new_config, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to write config: {e}")
        raise HTTPException(status_code=500, detail="Failed to save configuration")
        
    return {"message": "Configuration updated successfully", "config": new_config}
