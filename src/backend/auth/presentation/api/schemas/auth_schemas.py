"""Schemas for authentication API."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserSummaryResponse(BaseModel):
    """Authenticated user projection returned by auth endpoints."""

    id: UUID
    email: EmailStr
    display_name: str = Field(..., min_length=1, max_length=255)


class LoginRequest(BaseModel):
    """Credentials used for login."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "secret",
            },
        },
    )

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=255)


class RegisterRequest(BaseModel):
    """Payload for new user registration."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "display_name": "Ivan Petrov",
                "password": "secret123",
            },
        },
    )

    email: EmailStr
    display_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=255)


class RefreshTokenRequest(BaseModel):
    """Refresh token request payload."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"refresh_token": "<refresh-token>"},
        },
    )

    refresh_token: str = Field(..., min_length=1, max_length=512)


class LogoutRequest(BaseModel):
    """Logout request payload."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"refresh_token": "<refresh-token>"},
        },
    )

    refresh_token: str = Field(..., min_length=1, max_length=512)


class RefreshTokenResponse(BaseModel):
    """Token pair returned by refresh endpoint."""

    access_token: str
    refresh_token: str
    token_type: str = Field(default="Bearer")
    expires_in: int = Field(default=3600, ge=1)


class LoginResponse(RefreshTokenResponse):
    """Login response including current user projection."""

    user: UserSummaryResponse


class RegisterResponse(LoginResponse):
    """Registration response including current user projection."""
