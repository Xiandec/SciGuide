"""Workspace member domain entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from workspaces.domain.entities.workspace import WorkspaceRole


@dataclass(slots=True)
class WorkspaceMember:
    """Projection of a workspace member enriched with user profile data."""

    workspace_id: UUID
    user_id: UUID
    email: str | None
    display_name: str | None
    role: WorkspaceRole
    joined_at: datetime
