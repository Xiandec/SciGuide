"""Dependency wiring for messages use cases."""

from __future__ import annotations

from functools import lru_cache

from asyncpg import Pool
from fastapi import Depends

from auth.presentation.api.dependencies import get_db_pool
from config import settings
from messages.application.use_cases.create_message import CreateMessage
from messages.application.use_cases.list_messages import ListMessages
from messages.domain.repositories.message_repository import MessageRepository
from messages.domain.services.assistant_responder import AssistantResponder
from messages.infrastructure.llm import OpenRouterAssistantResponder
from messages.infrastructure.persistence import PostgresMessageRepository
from workspace_prompt.domain.repositories.workspace_prompt_repository import (
    WorkspacePromptRepository,
)
from workspace_prompt.presentation.api.dependencies import (
    get_workspace_prompt_repository,
)


def get_message_repository(
    pool: Pool = Depends(get_db_pool),
) -> MessageRepository:
    """Build message repository."""
    return PostgresMessageRepository(pool)


@lru_cache(maxsize=1)
def get_assistant_responder() -> AssistantResponder:
    """Build assistant responder service."""
    return OpenRouterAssistantResponder(
        api_key=settings.openrouter_api_key,
        model_name=settings.openrouter_model_name,
        base_url=settings.openrouter_base_url,
        request_timeout_seconds=settings.pipeline_request_timeout_seconds,
    )


def get_list_messages_use_case(
    message_repository: MessageRepository = Depends(get_message_repository),
) -> ListMessages:
    """Build list messages use case."""
    return ListMessages(message_repository=message_repository)


def get_create_message_use_case(
    message_repository: MessageRepository = Depends(get_message_repository),
    workspace_prompt_repository: WorkspacePromptRepository = Depends(
        get_workspace_prompt_repository,
    ),
    assistant_responder: AssistantResponder = Depends(
        get_assistant_responder,
    ),
) -> CreateMessage:
    """Build create message use case."""
    return CreateMessage(
        message_repository=message_repository,
        workspace_prompt_repository=workspace_prompt_repository,
        assistant_responder=assistant_responder,
    )
