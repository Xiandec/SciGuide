"""Dependency wiring for chat use cases."""

from __future__ import annotations

from asyncpg import Pool
from fastapi import Depends

from auth.presentation.api.dependencies import get_db_pool
from chats.application.use_cases.create_chat import CreateChat
from chats.application.use_cases.delete_chat import DeleteChat
from chats.application.use_cases.get_chat import GetChat
from chats.application.use_cases.list_chats import ListChats
from chats.application.use_cases.update_chat import UpdateChat
from chats.domain.repositories.chat_repository import ChatRepository
from chats.infrastructure.persistence import PostgresChatRepository
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)
from workspaces.presentation.api.dependencies import (
    get_workspace_repository,
)


def get_chat_repository(
    pool: Pool = Depends(get_db_pool),
) -> ChatRepository:
    """Build chat repository."""
    return PostgresChatRepository(pool)


def get_list_chats_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
    chat_repository: ChatRepository = Depends(get_chat_repository),
) -> ListChats:
    """Build list chats use case."""
    return ListChats(
        workspace_repository=workspace_repository,
        chat_repository=chat_repository,
    )


def get_create_chat_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
    chat_repository: ChatRepository = Depends(get_chat_repository),
) -> CreateChat:
    """Build create chat use case."""
    return CreateChat(
        workspace_repository=workspace_repository,
        chat_repository=chat_repository,
    )


def get_get_chat_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
    chat_repository: ChatRepository = Depends(get_chat_repository),
) -> GetChat:
    """Build get chat use case."""
    return GetChat(
        workspace_repository=workspace_repository,
        chat_repository=chat_repository,
    )


def get_update_chat_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
    chat_repository: ChatRepository = Depends(get_chat_repository),
) -> UpdateChat:
    """Build update chat use case."""
    return UpdateChat(
        workspace_repository=workspace_repository,
        chat_repository=chat_repository,
    )


def get_delete_chat_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
    chat_repository: ChatRepository = Depends(get_chat_repository),
) -> DeleteChat:
    """Build delete chat use case."""
    return DeleteChat(
        workspace_repository=workspace_repository,
        chat_repository=chat_repository,
    )
