from typing import Optional
from pydantic import BaseModel

class FirewallRuleCreate(BaseModel):
    rule_type: str  # ip, port, mac, rate_limit, time_based
    target: str
    device_id: Optional[str] = None
    direction: str = "both"
    action: str = "drop"
    schedule: Optional[str] = None
    expires_at: Optional[int] = None

class FirewallRuleResponse(BaseModel):
    id: str
    rule_type: str
    target: str
    device_id: Optional[str]
    direction: str
    action: str
    schedule: Optional[str]
    enabled: bool
    auto_block: bool
    created_at: int
    expires_at: Optional[int]

    class Config:
        from_attributes = True
