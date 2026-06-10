"""
NetWatch AI — Test Fixtures
Pytest configuration with async client, test database, and helper factories.
"""

import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Override database path BEFORE importing app modules
os.environ["SQLITE_DB_PATH"] = ":memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-unit-tests-only"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "adminpassword123"
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["REDIS_URL"] = "memory://"  # Use in-memory for slowapi during tests

from src.core.database import Base, engine, async_session, get_db
from src.core.models import User
from src.core.security import hash_password
from src.main import app


# ── Database fixtures ─────────────────────────


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create and tear down test database for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for direct DB operations in tests."""
    async with async_session() as session:
        yield session


# ── HTTP Client fixtures ──────────────────────


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP test client (unauthenticated)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user in the test database."""
    user = User(
        username="testadmin",
        email="testadmin@example.com",
        password_hash=hash_password("adminpass123"),
        role="admin",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def analyst_user(db_session: AsyncSession) -> User:
    """Create an analyst user in the test database."""
    user = User(
        username="testanalyst",
        email="analyst@example.com",
        password_hash=hash_password("analystpass123"),
        role="analyst",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def viewer_user(db_session: AsyncSession) -> User:
    """Create a viewer user in the test database."""
    user = User(
        username="testviewer",
        email="viewer@example.com",
        password_hash=hash_password("viewerpass123"),
        role="viewer",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ── Auth helper fixtures ──────────────────────


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    """Get a valid admin access token."""
    response = await client.post("/api/v1/auth/login", json={
        "username": "testadmin",
        "password": "adminpass123",
    })
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def analyst_token(client: AsyncClient, analyst_user: User) -> str:
    """Get a valid analyst access token."""
    response = await client.post("/api/v1/auth/login", json={
        "username": "testanalyst",
        "password": "analystpass123",
    })
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def viewer_token(client: AsyncClient, viewer_user: User) -> str:
    """Get a valid viewer access token."""
    response = await client.post("/api/v1/auth/login", json={
        "username": "testviewer",
        "password": "viewerpass123",
    })
    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    """Helper to create Authorization headers."""
    return {"Authorization": f"Bearer {token}"}
