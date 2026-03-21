"""Use case for deleting a personal chat."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from chats.application.use_cases._workspace_access import (
    get_workspace_access_or_raise,
)
from chats.domain.exceptions.chat_exceptions import ChatNotFoundError
from chats.domain.repositories.chat_repository import ChatRepository
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)


@dataclass(slots=True)
class DeleteChatRequest:
    """Delete chat request payload."""

    workspace_id: UUID
    chat_id: UUID
    actor_user_id: UUID


class DeleteChat:
    """Delete a chat owned by the current user."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        chat_repository: ChatRepository,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._chat_repository = chat_repository

    async def execute(self, request: DeleteChatRequest) -> None:
        """Delete the chat or raise if it does not exist."""
        await get_workspace_access_or_raise(
            workspace_repository=self._workspace_repository,
            workspace_id=request.workspace_id,
            user_id=request.actor_user_id,
        )

        deleted = await self._chat_repository.delete_owned(
            workspace_id=request.workspace_id,
            chat_id=request.chat_id,
            owner_user_id=request.actor_user_id,
        )
        if not deleted:
            raise ChatNotFoundError(request.chat_id)
