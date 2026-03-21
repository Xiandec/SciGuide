"""Workspace repository contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from workspaces.domain.entities.workspace import Workspace
from workspaces.domain.entities.workspace import WorkspaceAccess
from workspaces.domain.entities.workspace import WorkspaceType


class WorkspaceRepository(ABC):
    """Abstract persistence contract for workspaces."""

    @abstractmethod
    async def list_accessible(
        self,
        *,
        user_id: UUID,
        workspace_type: WorkspaceType | None,
        limit: int,
        cursor: str | None,
        sort_desc: bool,
    ) -> tuple[list[WorkspaceAccess], str | None, bool]:
        """List workspaces accessible to a user."""

    @abstractmethod
    async def create(self, workspace: Workspace) -> WorkspaceAccess:
        """Persist a workspace and return the owner projection."""

    @abstractmethod
    async def get_accessible_by_id(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
    ) -> WorkspaceAccess | None:
        """Load a single accessible workspace for a user."""

    @abstractmethod
    async def update_owned(
        self,
        *,
        workspace_id: UUID,
        owner_user_id: UUID,
        name: str,
        description: str | None,
    ) -> WorkspaceAccess | None:
        """Update a workspace owned by the actor."""

    @abstractmethod
    async def delete_owned(
        self,
        *,
        workspace_id: UUID,
        owner_user_id: UUID,
    ) -> bool:
        """Delete a workspace owned by the actor."""

    @abstractmethod
    async def delete_by_id(self, *, workspace_id: UUID) -> bool:
        """Delete a workspace by id for compensating actions."""
