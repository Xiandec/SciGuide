"""Chats API schemas."""

from chats.presentation.api.schemas.chat_schemas import ChatListResponse
from chats.presentation.api.schemas.chat_schemas import ChatResponse
from chats.presentation.api.schemas.chat_schemas import CreateChatRequest
from chats.presentation.api.schemas.chat_schemas import UpdateChatRequest

__all__ = [
    "ChatListResponse",
    "ChatResponse",
    "CreateChatRequest",
    "UpdateChatRequest",
]
