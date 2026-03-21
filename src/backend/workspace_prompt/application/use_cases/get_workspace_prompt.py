"""Use case for loading a workspace prompt."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from workspace_prompt.application.dto.workspace_prompt_dto import (
    WorkspacePromptDTO,
)
from workspace_prompt.domain.exceptions.workspace_prompt_exceptions import (
    WorkspacePromptNotFoundError,
)
from workspace_prompt.domain.repositories.workspace_prompt_repository import (
    WorkspacePromptRepository,
)


@dataclass(slots=True)
class GetWorkspacePromptRequest:
    """Get workspace prompt request payload."""

    workspace_id: UUID
    user_id: UUID


class GetWorkspacePrompt:
    """Load a workspace prompt accessible to the current user."""

    def __init__(
        self,
        workspace_prompt_repository: WorkspacePromptRepository,
    ) -> None:
        self._workspace_prompt_repository = workspace_prompt_repository

    async def execute(
        self,
        request: GetWorkspacePromptRequest,
    ) -> WorkspacePromptDTO:
        """Return prompt details or raise if inaccessible."""
        prompt_access = (
            await self._workspace_prompt_repository
            .get_accessible_by_workspace_id(
                workspace_id=request.workspace_id,
                user_id=request.user_id,
            )
        )
        if prompt_access is None:
            raise WorkspacePromptNotFoundError(request.workspace_id)

        return WorkspacePromptDTO.from_entity(prompt_access.prompt)
