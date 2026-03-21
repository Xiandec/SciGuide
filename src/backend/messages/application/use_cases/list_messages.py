"""Use case for listing chat messages."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from messages.application.dto.message_dto import MessageDTO
from messages.application.dto.message_dto import MessageListDTO
from messages.domain.exceptions.message_exceptions import (
    MessageChatNotFoundError,
)
from messages.domain.repositories.message_repository import MessageRepository


@dataclass(slots=True)
class ListMessagesRequest:
    """List messages request payload."""

    workspace_id: UUID
    chat_id: UUID
    actor_user_id: UUID
    limit: int
    cursor: str | None


class ListMessages:
    """List stored messages inside an accessible personal chat."""

    def __init__(self, message_repository: MessageRepository) -> None:
        self._message_repository = message_repository

    async def execute(
        self,
        request: ListMessagesRequest,
    ) -> MessageListDTO:
        """Return paginated chat messages."""
        chat_access = await self._message_repository.get_chat_access(
            workspace_id=request.workspace_id,
            chat_id=request.chat_id,
            user_id=request.actor_user_id,
        )
        if chat_access is None:
            raise MessageChatNotFoundError(request.chat_id)

        items, next_cursor, has_more = (
            await self._message_repository.list_by_chat(
                chat_id=request.chat_id,
                limit=request.limit,
                cursor=request.cursor,
            )
        )
        return MessageListDTO(
            items=[MessageDTO.from_entity(item) for item in items],
            next_cursor=next_cursor,
            has_more=has_more,
        )
