import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.security import get_current_user
from src.core.models import User
from src.firewall.schemas import FirewallRuleCreate, FirewallRuleResponse
from src.firewall.service import FirewallService

logger = logging.getLogger("netwatch.firewall.router")

router = APIRouter(prefix="/api/v1/firewall", tags=["firewall"])

def check_admin(current_user: User):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")

@router.get("/rules", response_model=List[FirewallRuleResponse])
async def list_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of active firewall rules."""
    check_admin(current_user)
    rules = await FirewallService.get_rules(db)
    return [FirewallRuleResponse.model_validate(r) for r in rules]

@router.post("/rules", response_model=FirewallRuleResponse)
async def create_rule(
    rule_in: FirewallRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new firewall rule."""
    check_admin(current_user)
    
    rule = await FirewallService.create_rule(
        db=db,
        rule_type=rule_in.rule_type,
        target=rule_in.target,
        device_id=rule_in.device_id,
        direction=rule_in.direction,
        action=rule_in.action,
        schedule=rule_in.schedule,
        auto_block=False,
        expires_at=rule_in.expires_at
    )
    return FirewallRuleResponse.model_validate(rule)

@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a firewall rule."""
    check_admin(current_user)
    
    success = await FirewallService.delete_rule(db, rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    return {"status": "success", "message": "Rule deleted"}
