"""
NetWatch AI — Flow Service
Business logic for traffic flow queries and statistics.
"""

import logging
from typing import Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Flow

logger = logging.getLogger("netwatch.flows")


class FlowService:
    """Handles traffic flow queries, search, and aggregation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_flows(
        self,
        page: int = 1,
        page_size: int = 50,
        device_id: str = None,
        protocol: str = None,
        threat_label: str = None,
    ) -> dict:
        """List flows with pagination and optional filters."""
        query = select(Flow)

        if device_id:
            query = query.where(Flow.device_id == device_id)
        if protocol:
            query = query.where(Flow.protocol == protocol)
        if threat_label:
            query = query.where(Flow.threat_label == threat_label)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Flow.time.desc()).limit(page_size).offset(offset)

        result = await self.db.execute(query)
        flows = result.scalars().all()

        return {
            "flows": flows,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def search_flows(self, query_text: str, limit: int = 50) -> list:
        """
        Full-text search over flows using SQLite FTS5.
        Note: FTS5 virtual table must be created by migration.
        Falls back to LIKE search if FTS5 not available.
        """
        try:
            # Try FTS5 first
            result = await self.db.execute(
                text(
                    "SELECT f.* FROM flows f "
                    "JOIN flows_fts fts ON f.id = fts.rowid "
                    "WHERE flows_fts MATCH :query "
                    "ORDER BY rank LIMIT :limit"
                ),
                {"query": query_text, "limit": limit},
            )
            return result.fetchall()
        except Exception:
            # Fallback to LIKE search
            result = await self.db.execute(
                select(Flow)
                .where(
                    Flow.domain.ilike(f"%{query_text}%")
                    | Flow.src_ip.ilike(f"%{query_text}%")
                    | Flow.dst_ip.ilike(f"%{query_text}%")
                    | Flow.threat_label.ilike(f"%{query_text}%")
                )
                .order_by(Flow.time.desc())
                .limit(limit)
            )
            return result.scalars().all()

    async def get_stats(self) -> dict:
        """Get aggregated flow statistics."""
        # Total counts
        total_result = await self.db.execute(
            select(
                func.count(Flow.id).label("total_flows"),
                func.coalesce(func.sum(Flow.bytes), 0).label("total_bytes"),
                func.coalesce(func.sum(Flow.packets), 0).label("total_packets"),
                func.count(func.distinct(Flow.device_id)).label("unique_devices"),
            )
        )
        stats = total_result.one()

        # Top domains
        top_domains_result = await self.db.execute(
            select(Flow.domain, func.count(Flow.id).label("count"))
            .where(Flow.domain.isnot(None))
            .group_by(Flow.domain)
            .order_by(func.count(Flow.id).desc())
            .limit(10)
        )
        top_domains = [
            {"domain": row[0], "count": row[1]}
            for row in top_domains_result.all()
        ]

        # Top countries
        top_countries_result = await self.db.execute(
            select(Flow.country, func.count(Flow.id).label("count"))
            .where(Flow.country.isnot(None))
            .group_by(Flow.country)
            .order_by(func.count(Flow.id).desc())
            .limit(10)
        )
        top_countries = [
            {"country": row[0], "count": row[1]}
            for row in top_countries_result.all()
        ]

        return {
            "total_flows": stats.total_flows,
            "total_bytes": stats.total_bytes,
            "total_packets": stats.total_packets,
            "unique_devices": stats.unique_devices,
            "top_domains": top_domains,
            "top_countries": top_countries,
        }

    async def get_top_domains(self, limit: int = 20) -> list:
        """Get top domains by traffic volume."""
        result = await self.db.execute(
            select(
                Flow.domain,
                func.count(Flow.id).label("flow_count"),
                func.coalesce(func.sum(Flow.bytes), 0).label("total_bytes"),
            )
            .where(Flow.domain.isnot(None))
            .group_by(Flow.domain)
            .order_by(func.sum(Flow.bytes).desc())
            .limit(limit)
        )
        return [
            {"domain": row[0], "flow_count": row[1], "total_bytes": row[2]}
            for row in result.all()
        ]
