"""Use case for listing personal chats in a workspace."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from chats.application.dto.chat_dto import ChatDTO
from chats.application.dto.chat_dto import ChatListDTO
from chats.application.use_cases._workspace_access import (
    get_workspace_access_or_raise,
)
from chats.domain.repositories.chat_repository import ChatRepository
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)


@dataclass(slots=True)
class ListChatsRequest:
    """List chats request payload."""

    workspace_id: UUID
    actor_user_id: UUID
    limit: int
    cursor: str | None
    sort: Literal["-updated_at", "updated_at"]


class ListChats:
    """List chats owned by the current user inside a workspace."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        chat_repository: ChatRepository,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._chat_repository = chat_repository

    async def execute(self, request: ListChatsRequest) -> ChatListDTO:
        """Return paginated personal chats for an accessible workspace."""
        await get_workspace_access_or_raise(
            workspace_repository=self._workspace_repository,
            workspace_id=request.workspace_id,
            user_id=request.actor_user_id,
        )

        items, next_cursor, has_more = (
            await self._chat_repository.list_owned_by_workspace(
                workspace_id=request.workspace_id,
                owner_user_id=request.actor_user_id,
                limit=request.limit,
                cursor=request.cursor,
                sort_desc=request.sort.startswith("-"),
            )
        )

        return ChatListDTO(
            items=[ChatDTO.from_entity(item) for item in items],
            next_cursor=next_cursor,
            has_more=has_more,
        )
