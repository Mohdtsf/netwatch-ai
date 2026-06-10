"""
NetWatch AI — Alert Router
REST endpoints for threat alert management.
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.alerts.schemas import AlertListResponse, AlertResponse, AlertStatsResponse
from src.alerts.service import AlertService
from src.core.database import get_db
from src.core.security import get_current_user, require_role

logger = logging.getLogger("netwatch.alerts.router")

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get(
    "",
    response_model=AlertListResponse,
    summary="List alerts",
)
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    severity: str = None,
    type: str = None,
    acknowledged: bool = None,
    current_user=Depends(require_role("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of alerts with optional filters."""
    service = AlertService(db)
    result = await service.list_alerts(
        page=page,
        page_size=page_size,
        severity=severity,
        alert_type=type,
        acknowledged=acknowledged,
    )
    return AlertListResponse(
        alerts=[AlertResponse.model_validate(a) for a in result["alerts"]],
        total=result["total"],
        unacknowledged=result["unacknowledged"],
    )


@router.get(
    "/stats",
    response_model=AlertStatsResponse,
    summary="Get alert statistics",
)
async def alert_stats(
    current_user=Depends(require_role("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated alert statistics broken down by severity and type."""
    service = AlertService(db)
    return await service.get_stats()


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Get alert details",
)
async def get_alert(
    alert_id: str,
    current_user=Depends(require_role("viewer")),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information about a specific alert."""
    service = AlertService(db)
    alert = await service.get_alert(alert_id)
    return AlertResponse.model_validate(alert)


@router.post(
    "/{alert_id}/acknowledge",
    response_model=AlertResponse,
    summary="Acknowledge an alert",
)
async def acknowledge_alert(
    alert_id: str,
    current_user=Depends(require_role("analyst")),
    db: AsyncSession = Depends(get_db),
):
    """Mark an alert as acknowledged/reviewed. Requires analyst role or higher."""
    service = AlertService(db)
    alert = await service.acknowledge_alert(alert_id, current_user.id)
    return AlertResponse.model_validate(alert)
