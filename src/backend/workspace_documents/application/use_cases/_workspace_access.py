"""Workspace access helpers for workspace documents use cases."""

from __future__ import annotations

from uuid import UUID

from workspaces.domain.entities.workspace import WorkspaceAccess
from workspaces.domain.entities.workspace import WorkspaceRole
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceNotFoundError,
)
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)
from workspace_documents.domain.exceptions.document_exceptions import (
    WorkspaceDocumentAccessDeniedError,
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


def ensure_workspace_admin(workspace_access: WorkspaceAccess) -> None:
    """Guard document management actions with admin role."""
    if workspace_access.my_role != WorkspaceRole.ADMIN:
        raise WorkspaceDocumentAccessDeniedError(
            "Only workspace administrators can manage documents",
        )
