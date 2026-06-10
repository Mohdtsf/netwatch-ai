"""
NetWatch AI — Auth Router
Authentication endpoints: register, login, refresh, logout, me.
"""

import logging

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from src.auth.service import AuthService
from src.core.config import settings
from src.core.database import get_db
from src.core.rate_limit import RATE_LOGIN, RATE_REGISTER, limiter
from src.core.redis import get_redis
from src.core.security import get_current_user
from fastapi_csrf_protect import CsrfProtect

logger = logging.getLogger("netwatch.auth.router")

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _get_auth_service(db: AsyncSession, redis=None) -> AuthService:
    return AuthService(db=db, redis=redis)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
@limiter.limit(RATE_REGISTER)
async def register(
    request: Request,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user account.
    The first user registered is automatically promoted to admin.
    """
    try:
        redis = await get_redis()
    except RuntimeError:
        redis = None

    service = _get_auth_service(db, redis)
    user = await service.register(data)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive tokens",
)
@limiter.limit(RATE_LOGIN)
async def login(
    request: Request,
    response: Response,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate with username and password.
    Returns access token in response body and refresh token as HttpOnly cookie.
    """
    try:
        redis = await get_redis()
    except RuntimeError:
        redis = None

    service = _get_auth_service(db, redis)
    access_token, refresh_token, user = await service.login(data)

    # Set refresh token as HttpOnly secure cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set True in production with HTTPS
        samesite="lax",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh_token(
    request: Request,
    response: Response,
    body: RefreshRequest = None,
    refresh_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh the access token using the refresh token.
    Accepts refresh token from HttpOnly cookie or request body.
    Implements token rotation — old refresh token is invalidated.
    """
    # Get refresh token from cookie or body
    token = refresh_token
    if not token and body:
        token = body.refresh_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )

    try:
        redis = await get_redis()
    except RuntimeError:
        redis = None

    service = _get_auth_service(db, redis)
    new_access, new_refresh = await service.refresh(token)

    # Rotate the HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )

    return TokenResponse(
        access_token=new_access,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout and invalidate refresh token",
)
async def logout(
    response: Response,
    current_user=Depends(get_current_user),
):
    """
    Invalidate the refresh token and clear the HttpOnly cookie.
    Requires valid access token.
    """
    try:
        redis = await get_redis()
    except RuntimeError:
        redis = None

    if redis:
        from src.auth.service import AuthService
        service = AuthService(db=None, redis=redis)
        await service.logout(current_user.id)

    # Clear cookie
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
    )

    return MessageResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(current_user=Depends(get_current_user)):
    """Return the authenticated user's profile information."""
    return UserResponse.model_validate(current_user)


@router.get(
    "/csrf-token",
    summary="Get CSRF token",
)
async def get_csrf_token(csrf_protect: CsrfProtect = Depends()):
    """Return a new CSRF token and set the CSRF cookie."""
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    csrf_protect.set_csrf_cookie(signed_token)
    return {"csrf_token": csrf_token}
