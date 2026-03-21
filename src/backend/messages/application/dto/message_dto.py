"""Message DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from messages.domain.entities.message import Message
from messages.domain.entities.message import MessageContextDocument
from messages.domain.entities.message import MessageRole
from messages.domain.entities.message import MessageStatus


@dataclass(slots=True)
class MessageDTO:
    """Message projection returned to presentation."""

    id: UUID
    chat_id: UUID
    role: MessageRole
    content: str
    status: MessageStatus
    created_at: datetime

    @classmethod
    def from_entity(cls, message: Message) -> "MessageDTO":
        """Map a message entity into API-facing DTO."""
        return cls(
            id=message.id,
            chat_id=message.chat_id,
            role=message.role,
            content=message.content,
            status=message.status,
            created_at=message.created_at,
        )


@dataclass(slots=True)
class MessageContextDocumentDTO:
    """Context document metadata returned to presentation."""

    document_id: UUID
    filename: str

    @classmethod
    def from_entity(
        cls,
        document: MessageContextDocument,
    ) -> "MessageContextDocumentDTO":
        """Map one attached context document."""
        return cls(
            document_id=document.document_id,
            filename=document.filename,
        )


@dataclass(slots=True)
class MessageListDTO:
    """Paginated message collection."""

    items: list[MessageDTO]
    next_cursor: str | None
    has_more: bool


@dataclass(slots=True)
class CreateMessageDTO:
    """Atomic user-assistant exchange result."""

    user_message: MessageDTO
    assistant_message: MessageDTO
    context_documents: list[MessageContextDocumentDTO]
