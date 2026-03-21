"""No-op lifecycle manager for local development."""

from __future__ import annotations

from workspaces.domain.entities.workspace import Workspace
from workspaces.domain.services.workspace_lifecycle_manager import (
    WorkspaceLifecycleManager,
)


class NoOpWorkspaceLifecycleManager(WorkspaceLifecycleManager):
    """Skip external lifecycle operations when integrations are disabled."""

    async def provision(self, workspace: Workspace) -> None:
        """Do nothing."""

    async def teardown(self, workspace: Workspace) -> None:
        """Do nothing."""
