"""
NetWatch AI — Auth Service
Business logic for user registration, login, token management.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import LoginRequest, RegisterRequest
from src.core.config import settings
from src.core.models import User
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger("netwatch.auth")


class AuthService:
    """Handles all authentication and user management logic."""

    def __init__(self, db: AsyncSession, redis=None):
        self.db = db
        self.redis = redis

    async def register(self, data: RegisterRequest) -> User:
        """Register a new user account."""
        # Check username uniqueness
        result = await self.db.execute(
            select(User).where(User.username == data.username)
        )
        if result.scalar_one_or_none():
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )

        # Check email uniqueness
        result = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        if result.scalar_one_or_none():
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        # Determine role: first user gets admin
        user_count = await self.db.execute(select(func.count(User.id)))
        count = user_count.scalar() or 0
        role = "admin" if count == 0 else "viewer"

        # Create user
        user = User(
            username=data.username,
            email=data.email,
            password_hash=hash_password(data.password),
            role=role,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"User registered: {user.username} (role={role})")
        return user

    async def login(self, data: LoginRequest) -> Tuple[str, str, User]:
        """Authenticate user and return access + refresh tokens."""
        from fastapi import HTTPException, status

        # Find user by username
        result = await self.db.execute(
            select(User).where(User.username == data.username)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        # Create tokens
        access_token = create_access_token(data={"sub": user.id})
        refresh_token = create_refresh_token(data={"sub": user.id})

        # Store refresh token hash in Redis for validation
        if self.redis:
            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            await self.redis.setex(
                f"refresh:{user.id}",
                settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
                token_hash,
            )

        logger.info(f"User logged in: {user.username}")
        return access_token, refresh_token, user

    async def refresh(self, refresh_token: str) -> Tuple[str, str]:
        """Validate refresh token and issue new token pair (token rotation)."""
        from fastapi import HTTPException, status

        # Decode the refresh token
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type — expected refresh token",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # Verify refresh token hash in Redis
        if self.redis:
            stored_hash = await self.redis.get(f"refresh:{user_id}")
            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            if not stored_hash or stored_hash != token_hash:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token revoked or expired",
                )

        # Verify user still exists
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        # Rotate: issue new tokens and invalidate old
        new_access = create_access_token(data={"sub": user.id})
        new_refresh = create_refresh_token(data={"sub": user.id})

        if self.redis:
            new_hash = hashlib.sha256(new_refresh.encode()).hexdigest()
            await self.redis.setex(
                f"refresh:{user.id}",
                settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
                new_hash,
            )

        logger.info(f"Token refreshed for user: {user.username}")
        return new_access, new_refresh

    async def logout(self, user_id: str):
        """Invalidate the user's refresh token."""
        if self.redis:
            await self.redis.delete(f"refresh:{user_id}")
        logger.info(f"User logged out: {user_id}")

    async def create_initial_admin(self):
        """Create the initial admin user from environment variables if no users exist."""
        user_count = await self.db.execute(select(func.count(User.id)))
        count = user_count.scalar() or 0

        if count > 0:
            return  # Users already exist

        admin = User(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role="admin",
        )
        self.db.add(admin)
        await self.db.commit()
        logger.info(f"✅ Initial admin user created: {settings.ADMIN_USERNAME}")
