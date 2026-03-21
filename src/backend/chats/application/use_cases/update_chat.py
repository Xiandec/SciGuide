"""Use case for updating chat metadata."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from chats.application.dto.chat_dto import ChatDTO
from chats.application.use_cases._workspace_access import (
    get_workspace_access_or_raise,
)
from chats.domain.entities.chat import Chat
from chats.domain.exceptions.chat_exceptions import ChatNotFoundError
from chats.domain.repositories.chat_repository import ChatRepository
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)


@dataclass(slots=True)
class UpdateChatRequest:
    """Update chat request payload."""

    workspace_id: UUID
    chat_id: UUID
    actor_user_id: UUID
    title: str


class UpdateChat:
    """Update title of a personal chat."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        chat_repository: ChatRepository,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._chat_repository = chat_repository

    async def execute(self, request: UpdateChatRequest) -> ChatDTO:
        """Update chat title or raise if chat is absent."""
        await get_workspace_access_or_raise(
            workspace_repository=self._workspace_repository,
            workspace_id=request.workspace_id,
            user_id=request.actor_user_id,
        )

        updated_chat = await self._chat_repository.update_owned_title(
            workspace_id=request.workspace_id,
            chat_id=request.chat_id,
            owner_user_id=request.actor_user_id,
            title=Chat.normalize_title(request.title),
        )
        if updated_chat is None:
            raise ChatNotFoundError(request.chat_id)

        return ChatDTO.from_entity(updated_chat)
