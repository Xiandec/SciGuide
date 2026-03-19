"""Schemas for mock messages API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from shared.presentation.api.schemas.common import CursorPage
from shared.presentation.api.schemas.common import MessageContextResponse


class MessageRole(str, Enum):
    """Allowed message role values."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    """Allowed message status values."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageResponse(BaseModel):
    """Message projection."""

    id: UUID
    chat_id: UUID
    role: MessageRole
    content: str = Field(..., min_length=0, max_length=20000)
    status: MessageStatus
    created_at: datetime


class MessageListResponse(BaseModel):
    """Paginated list of chat messages."""

    items: list[MessageResponse]
    page: CursorPage


class CreateMessageRequest(BaseModel):
    """Request payload for sending a new message."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"content": "Explain graph-guided retrieval."},
        },
    )

    content: str = Field(..., min_length=1, max_length=20000)


class CreateMessageResponse(BaseModel):
    """Atomic response for user message creation and assistant answer."""

    user_message: MessageResponse
    assistant_message: MessageResponse
    context: MessageContextResponse | None = None
