"""Contracts for workspace external storage lifecycle."""

from __future__ import annotations

from abc import ABC, abstractmethod

from workspaces.domain.entities.workspace import Workspace


class WorkspaceLifecycleManager(ABC):
    """Provision and destroy workspace resources in external storages."""

    @abstractmethod
    async def provision(self, workspace: Workspace) -> None:
        """Create workspace-specific external structures."""

    @abstractmethod
    async def teardown(self, workspace: Workspace) -> None:
        """Delete workspace-specific external structures."""
