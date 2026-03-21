"""Message domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class MessageRole(str, Enum):
    """Supported chat message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    """Supported chat message processing statuses."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class Message:
    """Message stored inside one personal chat."""

    id: UUID
    chat_id: UUID
    role: MessageRole
    content: str
    status: MessageStatus
    created_at: datetime
    error_message: str | None = None

    def __post_init__(self) -> None:
        """Validate message invariants."""
        visible_content = self.content.strip()
        if self.error_message is not None:
            self.error_message = self.error_message.strip() or None

        if len(self.content) > 20_000:
            raise ValueError("Message content cannot exceed 20000 characters")

        if self.role == MessageRole.USER and not visible_content:
            raise ValueError("User message content cannot be empty")

        if self.status == MessageStatus.COMPLETED and not visible_content:
            raise ValueError("Completed message content cannot be empty")

        if self.status == MessageStatus.FAILED and self.error_message is None:
            raise ValueError("Failed message must include an error message")


@dataclass(slots=True)
class MessageContextDocument:
    """Document reference attached to an assistant message."""

    document_id: UUID
    filename: str
    rank: int
    excerpt: str | None = None

    def __post_init__(self) -> None:
        """Validate attached context metadata."""
        self.filename = self.filename.strip()
        if self.excerpt is not None:
            self.excerpt = self.excerpt.strip() or None

        if not self.filename:
            raise ValueError("Context document filename cannot be empty")
        if self.rank < 1:
            raise ValueError("Context document rank must be positive")


@dataclass(slots=True)
class ChatAccess:
    """Accessible personal chat projection for the actor."""

    workspace_id: UUID
    chat_id: UUID
    owner_user_id: UUID
