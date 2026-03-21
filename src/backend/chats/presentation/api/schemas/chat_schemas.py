"""Schemas for chats API."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from shared.presentation.api.schemas.common import CursorPage


class ChatResponse(BaseModel):
    """Chat projection."""

    id: UUID
    workspace_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None = None


class ChatListResponse(BaseModel):
    """Paginated list of chats."""

    items: list[ChatResponse]
    page: CursorPage


class CreateChatRequest(BaseModel):
    """Request payload for chat creation."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"title": "Methods discussion"}},
    )

    title: str = Field(..., min_length=1, max_length=255)


class UpdateChatRequest(BaseModel):
    """Request payload for chat update."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"title": "Graph methods discussion"}},
    )

    title: str = Field(..., min_length=1, max_length=255)
