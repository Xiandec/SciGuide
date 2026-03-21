"""Use case for creating workspaces."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from workspaces.application.dto.workspace_dto import WorkspaceDTO
from workspaces.domain.entities.workspace import Workspace
from workspaces.domain.entities.workspace import WorkspaceAccessMode
from workspaces.domain.entities.workspace import WorkspaceType
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceLifecycleError,
)
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)
from workspaces.domain.services.workspace_lifecycle_manager import (
    WorkspaceLifecycleManager,
)


@dataclass(slots=True)
class CreateWorkspaceRequest:
    """Create workspace request payload."""

    owner_user_id: UUID
    name: str
    description: str | None
    workspace_type: WorkspaceType
    access_mode: WorkspaceAccessMode


class CreateWorkspace:
    """Create a workspace and provision external storages."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        lifecycle_manager: WorkspaceLifecycleManager,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._lifecycle_manager = lifecycle_manager

    async def execute(self, request: CreateWorkspaceRequest) -> WorkspaceDTO:
        """Create a workspace and reconcile its external resources."""
        timestamp = datetime.now(timezone.utc)
        workspace = Workspace(
            id=uuid4(),
            owner_user_id=request.owner_user_id,
            name=request.name,
            description=request.description,
            type=request.workspace_type,
            access_mode=request.access_mode,
            created_at=timestamp,
            updated_at=timestamp,
        )

        created_workspace = await self._workspace_repository.create(workspace)

        try:
            await self._lifecycle_manager.provision(
                created_workspace.workspace,
            )
        except WorkspaceLifecycleError:
            await self._workspace_repository.delete_by_id(
                workspace_id=created_workspace.workspace.id,
            )
            raise

        return WorkspaceDTO.from_access(created_workspace)
