"""Use case for creating chats."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from chats.application.dto.chat_dto import ChatDTO
from chats.application.use_cases._workspace_access import (
    get_workspace_access_or_raise,
)
from chats.domain.entities.chat import Chat
from chats.domain.repositories.chat_repository import ChatRepository
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)


@dataclass(slots=True)
class CreateChatRequest:
    """Create chat request payload."""

    workspace_id: UUID
    actor_user_id: UUID
    title: str


class CreateChat:
    """Create a personal chat in an accessible workspace."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        chat_repository: ChatRepository,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._chat_repository = chat_repository

    async def execute(self, request: CreateChatRequest) -> ChatDTO:
        """Create and persist a new chat."""
        await get_workspace_access_or_raise(
            workspace_repository=self._workspace_repository,
            workspace_id=request.workspace_id,
            user_id=request.actor_user_id,
        )

        timestamp = datetime.now(timezone.utc)
        chat = Chat(
            id=uuid4(),
            workspace_id=request.workspace_id,
            owner_user_id=request.actor_user_id,
            title=request.title,
            created_at=timestamp,
            updated_at=timestamp,
            last_message_at=None,
        )
        created_chat = await self._chat_repository.create(chat)
        return ChatDTO.from_entity(created_chat)
