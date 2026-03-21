"""Chats domain exceptions."""

from __future__ import annotations

from uuid import UUID


class ChatDomainError(Exception):
    """Base chat domain exception."""


class ChatNotFoundError(ChatDomainError):
    """Raised when a chat cannot be found for the current actor."""

    def __init__(self, chat_id: UUID) -> None:
        super().__init__(f"Chat {chat_id} was not found")
