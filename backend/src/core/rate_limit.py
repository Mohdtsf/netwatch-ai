"""
NetWatch AI — Rate Limiting
Redis-backed rate limiting via slowapi.
"""

import logging

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.core.config import settings

logger = logging.getLogger("netwatch.ratelimit")

# Create the limiter with Redis as the backend store
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    default_limits=["100/minute"],
    strategy="fixed-window",
)

# Rate limit constants for specific endpoints
is_test = settings.REDIS_URL == "memory://"
RATE_LOGIN = "1000/minute" if is_test else "5/minute"
RATE_REGISTER = "1000/minute" if is_test else "3/minute"
RATE_API = "10000/minute" if is_test else "100/minute"
RATE_WEBSOCKET = "1000/minute" if is_test else "10/minute"
