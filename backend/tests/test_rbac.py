"""
NetWatch AI — RBAC Tests
Test suite for role-based access control enforcement.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


# ═══════════════════════════════════════════════
# VIEWER ROLE TESTS
# ═══════════════════════════════════════════════


@pytest.mark.asyncio
async def test_viewer_can_access_viewer_endpoint(client: AsyncClient, viewer_token: str):
    """Viewer accessing viewer-level endpoint → 200."""
    response = await client.get(
        "/api/v1/devices",
        headers=auth_headers(viewer_token),
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_viewer_cannot_access_admin_endpoint(client: AsyncClient, viewer_token: str):
    """Viewer accessing admin-level endpoint → 403."""
    # Try to block a device (requires admin role)
    response = await client.post(
        "/api/v1/devices/fake-device-id/block",
        headers=auth_headers(viewer_token),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_viewer_cannot_access_analyst_endpoint(client: AsyncClient, viewer_token: str):
    """Viewer accessing analyst-level endpoint → 403."""
    # Try to trigger scan (requires analyst role)
    response = await client.get(
        "/api/v1/devices/scan",
        headers=auth_headers(viewer_token),
    )
    assert response.status_code == 403


# ═══════════════════════════════════════════════
# ANALYST ROLE TESTS
# ═══════════════════════════════════════════════


@pytest.mark.asyncio
async def test_analyst_can_access_analyst_endpoint(client: AsyncClient, analyst_token: str):
    """Analyst accessing analyst-level endpoint → 200."""
    response = await client.get(
        "/api/v1/devices/scan",
        headers=auth_headers(analyst_token),
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_analyst_can_access_viewer_endpoint(client: AsyncClient, analyst_token: str):
    """Analyst accessing viewer-level endpoint → 200 (higher role)."""
    response = await client.get(
        "/api/v1/devices",
        headers=auth_headers(analyst_token),
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_analyst_cannot_access_admin_endpoint(client: AsyncClient, analyst_token: str):
    """Analyst accessing admin-level endpoint → 403."""
    response = await client.post(
        "/api/v1/devices/fake-device-id/block",
        headers=auth_headers(analyst_token),
    )
    assert response.status_code == 403


# ═══════════════════════════════════════════════
# ADMIN ROLE TESTS
# ═══════════════════════════════════════════════


@pytest.mark.asyncio
async def test_admin_can_access_all_endpoints(client: AsyncClient, admin_token: str):
    """Admin accessing all role levels → 200."""
    # Viewer endpoint
    response = await client.get(
        "/api/v1/devices",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200

    # Analyst endpoint
    response = await client.get(
        "/api/v1/devices/scan",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200


# ═══════════════════════════════════════════════
# UNAUTHENTICATED TESTS
# ═══════════════════════════════════════════════


@pytest.mark.asyncio
async def test_unauthenticated_access_denied(client: AsyncClient):
    """Accessing protected endpoint without token → 401."""
    response = await client.get("/api/v1/devices")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_expired_token_denied(client: AsyncClient):
    """Accessing protected endpoint with invalid token → 401."""
    response = await client.get(
        "/api/v1/devices",
        headers=auth_headers("expired.fake.token"),
    )
    assert response.status_code == 401
