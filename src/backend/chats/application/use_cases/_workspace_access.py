"""Workspace access helpers for chats use cases."""

from __future__ import annotations

from uuid import UUID

from workspaces.domain.entities.workspace import WorkspaceAccess
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceNotFoundError,
)
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)


async def get_workspace_access_or_raise(
    *,
    workspace_repository: WorkspaceRepository,
    workspace_id: UUID,
    user_id: UUID,
) -> WorkspaceAccess:
    """Load workspace access or fail with workspace-level 404."""
    workspace_access = await workspace_repository.get_accessible_by_id(
        workspace_id=workspace_id,
        user_id=user_id,
    )
    if workspace_access is None:
        raise WorkspaceNotFoundError(workspace_id)

    return workspace_access
