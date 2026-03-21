"""Schemas for workspaces API."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from shared.presentation.api.schemas.common import CursorPage
from workspaces.domain.entities.workspace import WorkspaceAccessMode
from workspaces.domain.entities.workspace import WorkspaceRole
from workspaces.domain.entities.workspace import WorkspaceType


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
