"""
NetWatch AI — Redis Connection Manager
Async Redis client for session storage, rate limiting, and caching.
"""

import logging
from typing import Optional

import redis.asyncio as redis

from src.core.config import settings

logger = logging.getLogger("netwatch.redis")

redis_client: Optional[redis.Redis] = None


async def init_redis() -> redis.Redis:
    """Initialize the async Redis connection pool."""
    global redis_client
    if settings.REDIS_URL == "memory://":
        logger.warning("Using memory:// for REDIS_URL — Redis disabled (testing mode)")
        redis_client = None
        return None

    redis_client = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    # Verify connectivity
    await redis_client.ping()
    logger.info(f"✅ Redis connected at {settings.REDIS_URL}")
    return redis_client


async def close_redis():
    """Close the Redis connection pool."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
        logger.info("Redis connection closed")


async def get_redis() -> redis.Redis:
    """Dependency injection for Redis client."""
    if not redis_client:
        raise RuntimeError("Redis not initialized — call init_redis() first")
    return redis_client
