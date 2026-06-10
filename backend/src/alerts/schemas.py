"""
NetWatch AI — Alert Pydantic Schemas
Request/response models for alert management endpoints.
"""

from pydantic import BaseModel
from typing import Optional


class AlertResponse(BaseModel):
    """Single alert record."""
    id: str
    time: int
    severity: str
    type: str
    message: Optional[str] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    device_id: Optional[str] = None
    auto_blocked: bool = False
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[int] = None

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    """Paginated alert list."""
    alerts: list[AlertResponse]
    total: int
    unacknowledged: int


class AlertStatsResponse(BaseModel):
    """Aggregated alert statistics."""
    total: int
    by_severity: dict
    by_type: dict
    unacknowledged: int
    auto_blocked: int
