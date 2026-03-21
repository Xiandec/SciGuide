"""Chats domain exceptions."""

from chats.domain.exceptions.chat_exceptions import ChatDomainError
from chats.domain.exceptions.chat_exceptions import ChatNotFoundError

__all__ = ["ChatDomainError", "ChatNotFoundError"]
