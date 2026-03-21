"""Schemas for mock workspace members API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MemberRole(str, Enum):
    """Allowed workspace member roles."""

    ADMIN = "admin"
    USER = "user"


class WorkspaceMemberResponse(BaseModel):
    """Workspace member projection."""

    user_id: UUID
    email: EmailStr | None = None
    display_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    role: MemberRole
    joined_at: datetime


class WorkspaceMemberListResponse(BaseModel):
    """Workspace member collection."""

    items: list[WorkspaceMemberResponse]


class AddWorkspaceMemberRequest(BaseModel):
    """Request payload for adding a member."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "9b41e2d1-0c4b-40db-b80b-6bba9e6cd18e",
                "role": "user",
            },
        },
    )

    user_id: UUID
    role: MemberRole


class UpdateWorkspaceMemberRequest(BaseModel):
    """Request payload for changing a member role."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"role": "admin"}},
    )

    role: MemberRole
