"""
NetWatch AI — Flow Pydantic Schemas
Request/response models for traffic flow endpoints.
"""

from pydantic import BaseModel
from typing import Optional


class FlowResponse(BaseModel):
    """Single flow record."""
    id: int
    time: int
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    protocol: Optional[str] = None
    bytes: int = 0
    packets: int = 0
    domain: Optional[str] = None
    country: Optional[str] = None
    anomaly_score: float = 0.0
    threat_label: str = "Normal"
    device_id: Optional[str] = None

    model_config = {"from_attributes": True}


class FlowListResponse(BaseModel):
    """Paginated flow list."""
    flows: list[FlowResponse]
    total: int
    page: int
    page_size: int


class FlowStatsResponse(BaseModel):
    """Aggregated flow statistics."""
    total_flows: int
    total_bytes: int
    total_packets: int
    unique_devices: int
    top_domains: list[dict]
    top_countries: list[dict]
