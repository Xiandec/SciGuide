"""Assistant response generation contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from messages.domain.entities.message import Message
from messages.domain.entities.message import MessageContextDocument


@dataclass(slots=True)
class AssistantResponderRequest:
    """Input for assistant response generation."""

    workspace_id: UUID
    chat_id: UUID
    workspace_prompt: str
    message_history: tuple[Message, ...]
    user_message_content: str


@dataclass(slots=True)
class AssistantResponse:
    """Generated assistant response with retrieval metadata."""

    content: str
    documents_used: tuple[MessageContextDocument, ...]


class AssistantResponder(ABC):
    """Generates assistant answers for chat messages."""

    @abstractmethod
    async def generate(
        self,
        request: AssistantResponderRequest,
    ) -> AssistantResponse:
        """Generate an assistant response for one user message."""
