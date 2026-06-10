"""
NetWatch AI — Database Configuration
SQLAlchemy async engine with SQLite WAL mode optimizations.
"""

import logging
import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event, text

from src.core.config import settings

logger = logging.getLogger("netwatch.db")


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# Build SQLite URL — resolve path and ensure parent directory exists
_db_path = settings.SQLITE_DB_PATH

# If the path is absolute and starts with /app/ (Docker), adapt for local dev
if _db_path.startswith("/app/") and not os.path.exists("/app"):
    # Running locally — use path relative to the backend directory
    _db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data",
        "netwatch.db",
    )

# Ensure the parent directory exists
Path(_db_path).parent.mkdir(parents=True, exist_ok=True)

_db_url = f"sqlite+aiosqlite:///{_db_path}"

engine = create_async_engine(
    _db_url,
    echo=False,
    connect_args={"check_same_thread": False},
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def _set_sqlite_pragmas(dbapi_conn, connection_record):
    """Apply SQLite performance pragmas on every new connection."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.execute(f"PRAGMA cache_size = -{settings.SQLITE_CACHE_SIZE_MB * 1000}")
    cursor.execute("PRAGMA temp_store = MEMORY")
    cursor.execute("PRAGMA mmap_size = 536870912")  # 512 MB
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


# Apply pragmas to the sync engine underlying the async engine
event.listen(engine.sync_engine, "connect", _set_sqlite_pragmas)


async def init_db():
    """Create all tables if they don't exist."""
    # Import all models so they register with Base.metadata
    from src.core import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info(f"Database initialized at {settings.SQLITE_DB_PATH}")


async def close_db():
    """Close the database engine."""
    await engine.dispose()
    logger.info("Database connection closed")


async def get_db() -> AsyncSession:
    """Dependency injection for database sessions."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
