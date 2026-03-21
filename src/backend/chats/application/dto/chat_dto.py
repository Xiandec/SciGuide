"""Chat DTOs used by the application layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from chats.domain.entities.chat import Chat


@dataclass(slots=True)
class ChatDTO:
    """Chat payload returned to presentation."""

    id: UUID
    workspace_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None

    @classmethod
    def from_entity(cls, chat: Chat) -> "ChatDTO":
        """Build DTO from chat entity."""
        return cls(
            id=chat.id,
            workspace_id=chat.workspace_id,
            title=chat.title,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            last_message_at=chat.last_message_at,
        )


@dataclass(slots=True)
class ChatListDTO:
    """Paginated chat collection."""

    items: list[ChatDTO]
    next_cursor: str | None
    has_more: bool
