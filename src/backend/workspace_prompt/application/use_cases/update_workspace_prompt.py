"""Use case for updating a workspace prompt."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from workspace_prompt.application.dto.workspace_prompt_dto import (
    WorkspacePromptDTO,
)
from workspace_prompt.domain.entities.workspace_prompt import WorkspacePrompt
from workspace_prompt.domain.exceptions.workspace_prompt_exceptions import (
    WorkspacePromptAccessDeniedError,
)
from workspace_prompt.domain.exceptions.workspace_prompt_exceptions import (
    WorkspacePromptNotFoundError,
)
from workspace_prompt.domain.repositories.workspace_prompt_repository import (
    WorkspacePromptRepository,
)


@dataclass(slots=True)
class UpdateWorkspacePromptRequest:
    """Update workspace prompt request payload."""

    workspace_id: UUID
    actor_user_id: UUID
    content: str


class UpdateWorkspacePrompt:
    """Update a workspace prompt for an administrator."""

    def __init__(
        self,
        workspace_prompt_repository: WorkspacePromptRepository,
    ) -> None:
        self._workspace_prompt_repository = workspace_prompt_repository

    async def execute(
        self,
        request: UpdateWorkspacePromptRequest,
    ) -> WorkspacePromptDTO:
        """Update prompt content when the actor can manage it."""
        prompt_access = (
            await self._workspace_prompt_repository
            .get_accessible_by_workspace_id(
                workspace_id=request.workspace_id,
                user_id=request.actor_user_id,
            )
        )
        if prompt_access is None:
            raise WorkspacePromptNotFoundError(request.workspace_id)

        if not prompt_access.can_manage:
            raise WorkspacePromptAccessDeniedError(
                "Only workspace administrators can update the prompt",
            )

        updated_prompt = WorkspacePrompt(
            workspace_id=prompt_access.prompt.workspace_id,
            content=request.content,
            created_at=prompt_access.prompt.created_at,
            updated_at=prompt_access.prompt.updated_at,
            updated_by=request.actor_user_id,
        )
        persisted_prompt = (
            await self._workspace_prompt_repository.update_content(
                workspace_id=request.workspace_id,
                content=updated_prompt.content,
                updated_by=request.actor_user_id,
            )
        )
        if persisted_prompt is None:
            raise WorkspacePromptNotFoundError(request.workspace_id)

        return WorkspacePromptDTO.from_entity(persisted_prompt)
