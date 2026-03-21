"""Helpers for validating workspace member management permissions."""

from __future__ import annotations

from uuid import UUID

from workspaces.domain.entities.workspace import WorkspaceAccess
from workspaces.domain.entities.workspace import WorkspaceRole
from workspaces.domain.entities.workspace import WorkspaceType
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceAccessDeniedError,
)
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceNotFoundError,
)
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)


async def get_workspace_for_member_management(
    *,
    workspace_repository: WorkspaceRepository,
    workspace_id: UUID,
    actor_user_id: UUID,
) -> WorkspaceAccess:
    """Return a shared workspace accessible to an admin actor."""
    workspace_access = await workspace_repository.get_accessible_by_id(
        workspace_id=workspace_id,
        user_id=actor_user_id,
    )
    if workspace_access is None:
        raise WorkspaceNotFoundError(workspace_id)

    if workspace_access.workspace.type != WorkspaceType.SHARED:
        raise WorkspaceAccessDeniedError(
            "Workspace members are available only for shared workspaces",
        )

    if workspace_access.my_role != WorkspaceRole.ADMIN:
        raise WorkspaceAccessDeniedError(
            "Only workspace admins can manage workspace members",
        )

    return workspace_access
