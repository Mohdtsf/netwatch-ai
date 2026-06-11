from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DnsRuleBase(BaseModel):
    device_id: Optional[str] = None
    domain_pattern: str
    action: str = "block"
    category: Optional[str] = None

class DnsRuleCreate(DnsRuleBase):
    pass

class DnsRuleResponse(DnsRuleBase):
    id: str
    created_by: Optional[str] = None
    created_at: int
    
    class Config:
        from_attributes = True

class DnsQueryResponse(BaseModel):
    id: int
    time: int
    device_id: Optional[str] = None
    src_ip: Optional[str] = None
    domain: Optional[str] = None
    action: str
    category: Optional[str] = None
    
    class Config:
        from_attributes = True
