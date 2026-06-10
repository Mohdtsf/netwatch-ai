"""
NetWatch AI — Alert Service
Business logic for threat alert management.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Alert

logger = logging.getLogger("netwatch.alerts")


class AlertService:
    """Handles alert queries, acknowledgement, and statistics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_alerts(
        self,
        page: int = 1,
        page_size: int = 50,
        severity: str = None,
        alert_type: str = None,
        acknowledged: bool = None,
    ) -> dict:
        """List alerts with pagination and optional filters."""
        query = select(Alert)

        if severity:
            query = query.where(Alert.severity == severity)
        if alert_type:
            query = query.where(Alert.type == alert_type)
        if acknowledged is not None:
            query = query.where(Alert.acknowledged == acknowledged)

        # Total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Unacknowledged count
        unack_result = await self.db.execute(
            select(func.count(Alert.id)).where(Alert.acknowledged == False)
        )
        unacknowledged = unack_result.scalar() or 0

        # Paginate
        offset = (page - 1) * page_size
        query = query.order_by(Alert.time.desc()).limit(page_size).offset(offset)

        result = await self.db.execute(query)
        alerts = result.scalars().all()

        return {
            "alerts": alerts,
            "total": total,
            "unacknowledged": unacknowledged,
        }

    async def get_alert(self, alert_id: str) -> Alert:
        """Get a single alert by ID."""
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found",
            )
        return alert

    async def acknowledge_alert(self, alert_id: str, user_id: str) -> Alert:
        """Mark an alert as acknowledged/reviewed."""
        alert = await self.get_alert(alert_id)
        alert.acknowledged = True
        alert.acknowledged_by = user_id
        alert.acknowledged_at = int(datetime.now(timezone.utc).timestamp())
        await self.db.commit()
        await self.db.refresh(alert)
        logger.info(f"Alert acknowledged: {alert.id} by user {user_id}")
        return alert

    async def get_stats(self) -> dict:
        """Get aggregated alert statistics."""
        # Total
        total_result = await self.db.execute(select(func.count(Alert.id)))
        total = total_result.scalar() or 0

        # By severity
        severity_result = await self.db.execute(
            select(Alert.severity, func.count(Alert.id))
            .group_by(Alert.severity)
        )
        by_severity = {row[0]: row[1] for row in severity_result.all() if row[0]}

        # By type
        type_result = await self.db.execute(
            select(Alert.type, func.count(Alert.id))
            .group_by(Alert.type)
        )
        by_type = {row[0]: row[1] for row in type_result.all() if row[0]}

        # Unacknowledged
        unack_result = await self.db.execute(
            select(func.count(Alert.id)).where(Alert.acknowledged == False)
        )
        unacknowledged = unack_result.scalar() or 0

        # Auto-blocked
        blocked_result = await self.db.execute(
            select(func.count(Alert.id)).where(Alert.auto_blocked == True)
        )
        auto_blocked = blocked_result.scalar() or 0

        return {
            "total": total,
            "by_severity": by_severity,
            "by_type": by_type,
            "unacknowledged": unacknowledged,
            "auto_blocked": auto_blocked,
        }
