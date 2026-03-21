"""Workspace prompt repository contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from workspace_prompt.domain.entities.workspace_prompt import (
    WorkspacePrompt,
)
from workspace_prompt.domain.entities.workspace_prompt import (
    WorkspacePromptAccess,
)


class WorkspacePromptRepository(ABC):
    """Abstract persistence contract for workspace prompts."""

    @abstractmethod
    async def get_accessible_by_workspace_id(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
    ) -> WorkspacePromptAccess | None:
        """Load a prompt if the user can access the workspace."""

    @abstractmethod
    async def update_content(
        self,
        *,
        workspace_id: UUID,
        content: str,
        updated_by: UUID,
    ) -> WorkspacePrompt | None:
        """Persist new prompt content and return the updated entity."""
