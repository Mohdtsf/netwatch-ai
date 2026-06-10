"""
NetWatch AI — Auth Pydantic Schemas
Request/response models for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """New user registration payload."""
    username: str = Field(..., min_length=3, max_length=64, examples=["johndoe"])
    email: EmailStr = Field(..., examples=["john@example.com"])
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """User login payload."""
    username: str = Field(..., examples=["johndoe"])
    password: str = Field(...)


class TokenResponse(BaseModel):
    """JWT token pair response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires


class RefreshRequest(BaseModel):
    """Refresh token payload (used when not sending via cookie)."""
    refresh_token: str


class UserResponse(BaseModel):
    """Public user profile."""
    id: str
    username: str
    email: str
    role: str
    created_at: int

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Generic success message."""
    message: str
