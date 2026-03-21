"""Message repository contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from messages.domain.entities.message import ChatAccess
from messages.domain.entities.message import Message
from messages.domain.entities.message import MessageContextDocument


class MessageRepository(ABC):
    """Abstract persistence contract for chat messages."""

    @abstractmethod
    async def get_chat_access(
        self,
        *,
        workspace_id: UUID,
        chat_id: UUID,
        user_id: UUID,
    ) -> ChatAccess | None:
        """Load an accessible personal chat for the actor."""

    @abstractmethod
    async def list_by_chat(
        self,
        *,
        chat_id: UUID,
        limit: int,
        cursor: str | None,
    ) -> tuple[list[Message], str | None, bool]:
        """List messages inside one chat."""

    @abstractmethod
    async def list_recent_by_chat(
        self,
        *,
        chat_id: UUID,
        limit: int,
    ) -> list[Message]:
        """Load the latest messages in chronological order."""

    @abstractmethod
    async def create_turn(
        self,
        *,
        user_message: Message,
        assistant_message: Message,
        context_documents: list[MessageContextDocument],
    ) -> tuple[Message, Message]:
        """Persist one user-assistant exchange atomically."""
