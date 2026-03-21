"""Use case for updating workspace metadata."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from workspaces.application.dto.workspace_dto import WorkspaceDTO
from workspaces.domain.entities.workspace import Workspace
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceAccessDeniedError,
)
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceNotFoundError,
)
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)


@dataclass(slots=True)
class UpdateWorkspaceRequest:
    """Update workspace request payload."""

    workspace_id: UUID
    actor_user_id: UUID
    name: str | None
    description: str | None


class UpdateWorkspace:
    """Update workspace metadata for the owner."""

    def __init__(self, workspace_repository: WorkspaceRepository) -> None:
        self._workspace_repository = workspace_repository

    async def execute(self, request: UpdateWorkspaceRequest) -> WorkspaceDTO:
        """Update a workspace when the actor owns it."""
        workspace_access = (
            await self._workspace_repository.get_accessible_by_id(
                workspace_id=request.workspace_id,
                user_id=request.actor_user_id,
            )
        )
        if workspace_access is None:
            raise WorkspaceNotFoundError(request.workspace_id)

        workspace = workspace_access.workspace
        if workspace.owner_user_id != request.actor_user_id:
            raise WorkspaceAccessDeniedError(
                "Only the workspace owner can update workspace metadata",
            )

        if request.name is None and request.description is None:
            return WorkspaceDTO.from_access(workspace_access)

        updated_entity = Workspace(
            id=workspace.id,
            owner_user_id=workspace.owner_user_id,
            name=request.name if request.name is not None else workspace.name,
            description=(
                request.description
                if request.description is not None
                else workspace.description
            ),
            type=workspace.type,
            access_mode=workspace.access_mode,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )
        updated_workspace = await self._workspace_repository.update_owned(
            workspace_id=workspace.id,
            owner_user_id=request.actor_user_id,
            name=updated_entity.name,
            description=updated_entity.description,
        )
        if updated_workspace is None:
            raise WorkspaceNotFoundError(request.workspace_id)

        return WorkspaceDTO.from_access(updated_workspace)
