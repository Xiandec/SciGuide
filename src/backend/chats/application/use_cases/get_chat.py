"""Use case for loading a personal chat."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from chats.application.dto.chat_dto import ChatDTO
from chats.application.use_cases._workspace_access import (
    get_workspace_access_or_raise,
)
from chats.domain.exceptions.chat_exceptions import ChatNotFoundError
from chats.domain.repositories.chat_repository import ChatRepository
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)


@dataclass(slots=True)
class GetChatRequest:
    """Get chat request payload."""

    workspace_id: UUID
    chat_id: UUID
    actor_user_id: UUID


class GetChat:
    """Load a chat owned by the current user."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        chat_repository: ChatRepository,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._chat_repository = chat_repository

    async def execute(self, request: GetChatRequest) -> ChatDTO:
        """Return chat details or raise if it does not exist."""
        await get_workspace_access_or_raise(
            workspace_repository=self._workspace_repository,
            workspace_id=request.workspace_id,
            user_id=request.actor_user_id,
        )

        chat = await self._chat_repository.get_owned_by_id(
            workspace_id=request.workspace_id,
            chat_id=request.chat_id,
            owner_user_id=request.actor_user_id,
        )
        if chat is None:
            raise ChatNotFoundError(request.chat_id)

        return ChatDTO.from_entity(chat)
