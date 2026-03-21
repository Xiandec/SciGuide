"""Use case for deleting workspaces."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceAccessDeniedError,
)
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceLifecycleError,
)
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceNotFoundError,
)
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)
from workspaces.domain.services.workspace_lifecycle_manager import (
    WorkspaceLifecycleManager,
)


@dataclass(slots=True)
class DeleteWorkspaceRequest:
    """Delete workspace request payload."""

    workspace_id: UUID
    actor_user_id: UUID


class DeleteWorkspace:
    """Delete a workspace and its external storage structures."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        lifecycle_manager: WorkspaceLifecycleManager,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._lifecycle_manager = lifecycle_manager

    async def execute(self, request: DeleteWorkspaceRequest) -> None:
        """Delete a workspace when the actor owns it."""
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
                "Only the workspace owner can delete the workspace",
            )

        await self._lifecycle_manager.teardown(workspace)
        deleted = await self._workspace_repository.delete_owned(
            workspace_id=request.workspace_id,
            owner_user_id=request.actor_user_id,
        )
        if deleted:
            return

        try:
            await self._lifecycle_manager.provision(workspace)
        except WorkspaceLifecycleError as exc:
            raise WorkspaceLifecycleError(
                "Workspace external resources were removed, "
                "but metadata rollback failed",
            ) from exc

        raise WorkspaceNotFoundError(request.workspace_id)
