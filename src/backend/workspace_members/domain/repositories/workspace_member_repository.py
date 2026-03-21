"""Workspace member repository contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from workspaces.domain.entities.workspace import WorkspaceRole
from workspace_members.domain.entities.workspace_member import (
    WorkspaceMember,
)


class WorkspaceMemberRepository(ABC):
    """Abstract persistence contract for workspace members."""

    @abstractmethod
    async def list_by_workspace(
        self,
        *,
        workspace_id: UUID,
    ) -> list[WorkspaceMember]:
        """List members of a workspace."""

    @abstractmethod
    async def get_by_workspace_and_user(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
    ) -> WorkspaceMember | None:
        """Load one member of a workspace."""

    @abstractmethod
    async def add(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
        role: WorkspaceRole,
    ) -> WorkspaceMember:
        """Add a member to a workspace."""

    @abstractmethod
    async def update_role(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
        role: WorkspaceRole,
    ) -> WorkspaceMember | None:
        """Update a member role."""

    @abstractmethod
    async def remove(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Remove a member from a workspace."""

    @abstractmethod
    async def count_admins(self, *, workspace_id: UUID) -> int:
        """Count workspace admins."""
