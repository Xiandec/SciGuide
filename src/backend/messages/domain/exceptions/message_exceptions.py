"""Message domain exceptions."""

from __future__ import annotations

from uuid import UUID


class MessageDomainError(Exception):
    """Base message domain exception."""


class MessageChatNotFoundError(MessageDomainError):
    """Raised when a chat cannot be found or accessed."""

    def __init__(self, chat_id: UUID) -> None:
        super().__init__(f"Chat {chat_id} was not found")


class MessageGenerationError(MessageDomainError):
    """Raised when assistant response generation fails."""

    def __init__(
        self,
        message: str = "Assistant response generation failed",
    ) -> None:
        super().__init__(message)
