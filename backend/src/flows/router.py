"""
NetWatch AI — Flow Router
REST endpoints for traffic flow queries.
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import require_role
from src.flows.schemas import FlowListResponse, FlowResponse, FlowStatsResponse
from src.flows.service import FlowService

logger = logging.getLogger("netwatch.flows.router")

router = APIRouter(prefix="/api/v1/flows", tags=["flows"])


@router.get(
    "",
    response_model=FlowListResponse,
    summary="List traffic flows",
)
async def list_flows(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    device_id: str = None,
    protocol: str = None,
    threat_label: str = None,
    current_user=Depends(require_role("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of traffic flows with optional filters."""
    service = FlowService(db)
    result = await service.list_flows(
        page=page,
        page_size=page_size,
        device_id=device_id,
        protocol=protocol,
        threat_label=threat_label,
    )
    return FlowListResponse(
        flows=[FlowResponse.model_validate(f) for f in result["flows"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get(
    "/search",
    summary="Full-text search flows",
)
async def search_flows(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(50, ge=1, le=200),
    current_user=Depends(require_role("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """Search flows using FTS5 full-text search (falls back to LIKE if FTS5 unavailable)."""
    service = FlowService(db)
    flows = await service.search_flows(q, limit=limit)
    return {"flows": flows, "total": len(flows), "query": q}


@router.get(
    "/stats",
    response_model=FlowStatsResponse,
    summary="Get flow statistics",
)
async def flow_stats(
    current_user=Depends(require_role("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated traffic flow statistics."""
    service = FlowService(db)
    return await service.get_stats()


@router.get(
    "/top-domains",
    summary="Top domains by traffic",
)
async def top_domains(
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(require_role("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """Get top domains ranked by traffic volume."""
    service = FlowService(db)
    return await service.get_top_domains(limit=limit)
