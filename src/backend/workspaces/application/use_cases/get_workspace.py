"""Use case for loading a workspace."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from workspaces.application.dto.workspace_dto import WorkspaceDTO
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceNotFoundError,
)
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)


@dataclass(slots=True)
class GetWorkspaceRequest:
    """Get workspace request payload."""

    workspace_id: UUID
    user_id: UUID


class GetWorkspace:
    """Load a workspace accessible to the current user."""

    def __init__(self, workspace_repository: WorkspaceRepository) -> None:
        self._workspace_repository = workspace_repository

    async def execute(self, request: GetWorkspaceRequest) -> WorkspaceDTO:
        """Return workspace details or raise if inaccessible."""
        workspace_access = (
            await self._workspace_repository.get_accessible_by_id(
                workspace_id=request.workspace_id,
                user_id=request.user_id,
            )
        )
        if workspace_access is None:
            raise WorkspaceNotFoundError(request.workspace_id)

        return WorkspaceDTO.from_access(workspace_access)
