"""Common API schemas shared across presentation modules."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CursorPage(BaseModel):
    """Cursor-based pagination metadata."""

    next_cursor: str | None = Field(default=None)
    has_more: bool = Field(default=False)


class ErrorDetails(BaseModel):
    """Standard error payload body."""

    code: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=500)
    details: Any | None = None
    request_id: UUID


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""

    error: ErrorDetails


class DocumentContextItem(BaseModel):
    """Document metadata used in generated answer context."""

    document_id: UUID
    filename: str = Field(..., min_length=1, max_length=255)


class MessageContextResponse(BaseModel):
    """Context metadata attached to generated assistant responses."""

    documents_used: list[DocumentContextItem] = Field(default_factory=list)


class EmptyResponse(BaseModel):
    """Empty schema kept for explicit OpenAPI usage when needed."""

    model_config = ConfigDict(extra="forbid")
