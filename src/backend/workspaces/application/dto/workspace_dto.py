"""Workspace DTOs used by the application layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from workspaces.domain.entities.workspace import Workspace
from workspaces.domain.entities.workspace import WorkspaceAccess
from workspaces.domain.entities.workspace import WorkspaceAccessMode
from workspaces.domain.entities.workspace import WorkspaceRole
from workspaces.domain.entities.workspace import WorkspaceType


@dataclass(slots=True)
class WorkspaceDTO:
    """Workspace payload returned to presentation."""

    id: UUID
    name: str
    description: str | None
    type: WorkspaceType
    access_mode: WorkspaceAccessMode
    my_role: WorkspaceRole
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_access(cls, workspace_access: WorkspaceAccess) -> "WorkspaceDTO":
        """Build DTO from a workspace access projection."""
        workspace = workspace_access.workspace
        return cls(
            id=workspace.id,
            name=workspace.name,
            description=workspace.description,
            type=workspace.type,
            access_mode=workspace.access_mode,
            my_role=workspace_access.my_role,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )

    @classmethod
    def from_workspace(
        cls,
        workspace: Workspace,
        *,
        my_role: WorkspaceRole,
    ) -> "WorkspaceDTO":
        """Build DTO from a plain workspace entity."""
        return cls(
            id=workspace.id,
            name=workspace.name,
            description=workspace.description,
            type=workspace.type,
            access_mode=workspace.access_mode,
            my_role=my_role,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )


@dataclass(slots=True)
class WorkspaceListDTO:
    """Paginated workspace collection."""

    items: list[WorkspaceDTO]
    next_cursor: str | None
    has_more: bool
