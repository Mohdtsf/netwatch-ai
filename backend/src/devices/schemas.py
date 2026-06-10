"""
NetWatch AI — Device Pydantic Schemas
Request/response models for device management endpoints.
"""

from pydantic import BaseModel
from typing import Optional


class DeviceResponse(BaseModel):
    """Single device representation."""
    id: str
    mac_address: str
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    device_type: str = "unknown"
    custom_name: Optional[str] = None
    vendor: Optional[str] = None
    os_type: Optional[str] = None
    first_seen: int
    last_seen: int
    is_blocked: bool = False
    is_online: bool = False
    vpn_enabled: bool = False
    risk_score: int = 0

    model_config = {"from_attributes": True}


class DeviceUpdateRequest(BaseModel):
    """Update device metadata."""
    custom_name: Optional[str] = None
    device_type: Optional[str] = None


class DeviceListResponse(BaseModel):
    """Paginated device list."""
    devices: list[DeviceResponse]
    total: int
    online: int
