"""Chat repository contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from chats.domain.entities.chat import Chat


class ChatRepository(ABC):
    """Abstract persistence contract for chats."""

    @abstractmethod
    async def list_owned_by_workspace(
        self,
        *,
        workspace_id: UUID,
        owner_user_id: UUID,
        limit: int,
        cursor: str | None,
        sort_desc: bool,
    ) -> tuple[list[Chat], str | None, bool]:
        """List chats owned by a user in a workspace."""

    @abstractmethod
    async def create(self, chat: Chat) -> Chat:
        """Persist a chat."""

    @abstractmethod
    async def get_owned_by_id(
        self,
        *,
        workspace_id: UUID,
        chat_id: UUID,
        owner_user_id: UUID,
    ) -> Chat | None:
        """Load a chat if it belongs to the current actor."""

    @abstractmethod
    async def update_owned_title(
        self,
        *,
        workspace_id: UUID,
        chat_id: UUID,
        owner_user_id: UUID,
        title: str,
    ) -> Chat | None:
        """Update chat title for the owner."""

    @abstractmethod
    async def delete_owned(
        self,
        *,
        workspace_id: UUID,
        chat_id: UUID,
        owner_user_id: UUID,
    ) -> bool:
        """Delete a chat owned by the actor."""
