"""Schemas for mock workspaces API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from shared.presentation.api.schemas.common import CursorPage


class WorkspaceType(str, Enum):
    """Allowed workspace type values."""

    PRIVATE = "private"
    SHARED = "shared"


class WorkspaceAccessMode(str, Enum):
    """Allowed workspace access modes."""

    OWNER_ONLY = "owner_only"
    BY_MEMBERSHIP = "by_membership"
    GLOBAL = "global"


class WorkspaceRole(str, Enum):
    """User role inside a workspace."""

    ADMIN = "admin"
    USER = "user"


class WorkspaceResponse(BaseModel):
    """Workspace projection returned by API."""

    id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    type: WorkspaceType
    access_mode: WorkspaceAccessMode
    my_role: WorkspaceRole
    created_at: datetime
    updated_at: datetime


class WorkspaceListResponse(BaseModel):
    """Paginated workspace collection."""

    items: list[WorkspaceResponse]
    page: CursorPage


class CreateWorkspaceRequest(BaseModel):
    """Workspace creation payload."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Graph Retrieval",
                "description": (
                    "Workspace for graph-guided retrieval experiments"
                ),
                "type": "shared",
                "access_mode": "by_membership",
            },
        },
    )

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    type: WorkspaceType
    access_mode: WorkspaceAccessMode


class UpdateWorkspaceRequest(BaseModel):
    """Workspace partial update payload."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Graph Retrieval Lab",
                "description": "Updated description",
            },
        },
    )

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
