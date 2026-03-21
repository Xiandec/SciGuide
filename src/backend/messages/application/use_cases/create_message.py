"""Use case for sending a message and generating an assistant reply."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from messages.application.dto.message_dto import CreateMessageDTO
from messages.application.dto.message_dto import MessageContextDocumentDTO
from messages.application.dto.message_dto import MessageDTO
from messages.domain.entities.message import Message
from messages.domain.entities.message import MessageRole
from messages.domain.entities.message import MessageStatus
from messages.domain.exceptions.message_exceptions import (
    MessageChatNotFoundError,
)
from messages.domain.exceptions.message_exceptions import (
    MessageGenerationError,
)
from messages.domain.repositories.message_repository import MessageRepository
from messages.domain.services.assistant_responder import AssistantResponder
from messages.domain.services.assistant_responder import (
    AssistantResponderRequest,
)
from workspace_prompt.domain.repositories.workspace_prompt_repository import (
    WorkspacePromptRepository,
)

DEFAULT_WORKSPACE_PROMPT = (
    "You are a scientific assistant. Answer only within the current "
    "workspace context."
)


@dataclass(slots=True)
class CreateMessageRequest:
    """Create message request payload."""

    workspace_id: UUID
    chat_id: UUID
    actor_user_id: UUID
    content: str


class CreateMessage:
    """Create one user message and an assistant response."""

    def __init__(
        self,
        message_repository: MessageRepository,
        workspace_prompt_repository: WorkspacePromptRepository,
        assistant_responder: AssistantResponder,
        history_limit: int = 20,
    ) -> None:
        self._message_repository = message_repository
        self._workspace_prompt_repository = workspace_prompt_repository
        self._assistant_responder = assistant_responder
        self._history_limit = history_limit

    async def execute(
        self,
        request: CreateMessageRequest,
    ) -> CreateMessageDTO:
        """Persist a chat exchange and return both stored messages."""
        content = request.content.strip()
        if not content:
            raise ValueError("Message content cannot be empty")

        chat_access = await self._message_repository.get_chat_access(
            workspace_id=request.workspace_id,
            chat_id=request.chat_id,
            user_id=request.actor_user_id,
        )
        if chat_access is None:
            raise MessageChatNotFoundError(request.chat_id)

        history = await self._message_repository.list_recent_by_chat(
            chat_id=request.chat_id,
            limit=self._history_limit,
        )
        workspace_prompt = await self._load_workspace_prompt(
            workspace_id=request.workspace_id,
            actor_user_id=request.actor_user_id,
        )

        user_created_at = datetime.now(UTC)
        assistant_created_at = user_created_at + timedelta(milliseconds=1)
        user_message = Message(
            id=uuid4(),
            chat_id=request.chat_id,
            role=MessageRole.USER,
            content=content,
            status=MessageStatus.COMPLETED,
            created_at=user_created_at,
        )

        try:
            response = await self._assistant_responder.generate(
                AssistantResponderRequest(
                    workspace_id=request.workspace_id,
                    chat_id=request.chat_id,
                    workspace_prompt=workspace_prompt,
                    message_history=tuple(history),
                    user_message_content=content,
                )
            )
            assistant_message = Message(
                id=uuid4(),
                chat_id=request.chat_id,
                role=MessageRole.ASSISTANT,
                content=response.content,
                status=MessageStatus.COMPLETED,
                created_at=assistant_created_at,
            )
            context_documents = list(response.documents_used)
        except Exception as exc:
            assistant_message = Message(
                id=uuid4(),
                chat_id=request.chat_id,
                role=MessageRole.ASSISTANT,
                content=(
                    "Не удалось сгенерировать ответ в контексте текущего "
                    "воркспейса."
                ),
                status=MessageStatus.FAILED,
                created_at=assistant_created_at,
                error_message=self._build_generation_error(exc),
            )
            context_documents = []

        stored_user, stored_assistant = (
            await self._message_repository.create_turn(
                user_message=user_message,
                assistant_message=assistant_message,
                context_documents=context_documents,
            )
        )

        return CreateMessageDTO(
            user_message=MessageDTO.from_entity(stored_user),
            assistant_message=MessageDTO.from_entity(stored_assistant),
            context_documents=[
                MessageContextDocumentDTO.from_entity(item)
                for item in context_documents
            ],
        )

    async def _load_workspace_prompt(
        self,
        *,
        workspace_id: UUID,
        actor_user_id: UUID,
    ) -> str:
        """Load a workspace prompt or fall back to the default text."""
        prompt_access = (
            await self._workspace_prompt_repository
            .get_accessible_by_workspace_id(
                workspace_id=workspace_id,
                user_id=actor_user_id,
            )
        )
        if prompt_access is None:
            return DEFAULT_WORKSPACE_PROMPT
        return prompt_access.prompt.content

    @staticmethod
    def _build_generation_error(error: Exception) -> str:
        """Normalize a generation failure for persistent storage."""
        if isinstance(error, MessageGenerationError):
            message = str(error).strip()
        else:
            message = str(error).strip() or error.__class__.__name__
        return message[:4000]
