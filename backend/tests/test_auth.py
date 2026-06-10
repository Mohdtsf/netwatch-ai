"""
NetWatch AI — Auth Tests
Test suite for registration, login, token refresh, logout, and profile endpoints.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


# ═══════════════════════════════════════════════
# REGISTRATION TESTS
# ═══════════════════════════════════════════════


@pytest.mark.asyncio
async def test_register_new_user(client: AsyncClient):
    """Register a new user → 201 + UserResponse."""
    response = await client.post("/api/v1/auth/register", json={
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "securepass123",
    })
    print("RESPONSE:", response.json())
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    # First user should be admin
    assert data["role"] == "admin"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_register_second_user_is_viewer(client: AsyncClient):
    """Second user registered should be viewer, not admin."""
    # First user (becomes admin)
    await client.post("/api/v1/auth/register", json={
        "username": "firstuser",
        "email": "first@example.com",
        "password": "securepass123",
    })
    # Second user (should be viewer)
    response = await client.post("/api/v1/auth/register", json={
        "username": "seconduser",
        "email": "second@example.com",
        "password": "securepass123",
    })
    assert response.status_code == 201
    assert response.json()["role"] == "viewer"


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    """Register with duplicate username → 409."""
    await client.post("/api/v1/auth/register", json={
        "username": "duplicate",
        "email": "first@example.com",
        "password": "securepass123",
    })
    response = await client.post("/api/v1/auth/register", json={
        "username": "duplicate",
        "email": "different@example.com",
        "password": "securepass123",
    })
    assert response.status_code == 409
    assert "username" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Register with duplicate email → 409."""
    await client.post("/api/v1/auth/register", json={
        "username": "user1",
        "email": "same@example.com",
        "password": "securepass123",
    })
    response = await client.post("/api/v1/auth/register", json={
        "username": "user2",
        "email": "same@example.com",
        "password": "securepass123",
    })
    assert response.status_code == 409
    assert "email" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """Register with password less than 8 chars → 422."""
    response = await client.post("/api/v1/auth/register", json={
        "username": "weakuser",
        "email": "weak@example.com",
        "password": "short",
    })
    assert response.status_code == 422


# ═══════════════════════════════════════════════
# LOGIN TESTS
# ═══════════════════════════════════════════════


@pytest.mark.asyncio
async def test_login_valid_credentials(client: AsyncClient, admin_user):
    """Login with valid credentials → 200 + tokens."""
    response = await client.post("/api/v1/auth/login", json={
        "username": "testadmin",
        "password": "adminpass123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, admin_user):
    """Login with wrong password → 401."""
    response = await client.post("/api/v1/auth/login", json={
        "username": "testadmin",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Login with nonexistent username → 401."""
    response = await client.post("/api/v1/auth/login", json={
        "username": "nonexistent",
        "password": "anypassword",
    })
    assert response.status_code == 401


# ═══════════════════════════════════════════════
# TOKEN / ME TESTS
# ═══════════════════════════════════════════════


@pytest.mark.asyncio
async def test_me_with_valid_token(client: AsyncClient, admin_token: str):
    """GET /me with valid token → 200 + user data."""
    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testadmin"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_me_without_token(client: AsyncClient):
    """GET /me without token → 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token(client: AsyncClient):
    """GET /me with garbage token → 401."""
    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers("invalid.token.here"),
    )
    assert response.status_code == 401


# ═══════════════════════════════════════════════
# LOGOUT TESTS
# ═══════════════════════════════════════════════


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, admin_token: str):
    """POST /logout with valid token → 200."""
    response = await client.post(
        "/api/v1/auth/logout",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"
