"""
NetWatch AI — Health Check Tests
Test suite for health and system info endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """GET /health → 200 + correct payload structure."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["service"] == "netwatch-backend"
    assert data["version"] == "0.1.0"
    assert "components" in data
    assert "database" in data["components"]
    assert "scheduler" in data["components"]


@pytest.mark.asyncio
async def test_system_info(client: AsyncClient):
    """GET /api/v1/system/info → 200 + system metadata."""
    response = await client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "NetWatch AI"
    assert data["version"] == "0.1.0"
    assert "profile" in data
    assert "ml_enabled" in data
    assert "endpoints" in data


@pytest.mark.asyncio
async def test_docs_endpoint(client: AsyncClient):
    """GET /docs → 200 (Swagger UI)."""
    response = await client.get("/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_redoc_endpoint(client: AsyncClient):
    """GET /redoc → 200 (ReDoc UI)."""
    response = await client.get("/redoc")
    assert response.status_code == 200
