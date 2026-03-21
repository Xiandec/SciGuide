"""Schemas for workspace documents API."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from shared.presentation.api.schemas.common import CursorPage
from workspace_documents.domain.entities.workspace_document import (
    DocumentStage,
)
from workspace_documents.domain.entities.workspace_document import (
    DocumentStatus,
)


class WorkspaceDocumentResponse(BaseModel):
    """Workspace document projection."""

    id: UUID
    workspace_id: UUID
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., min_length=1, max_length=255)
    size_bytes: int = Field(..., ge=0)
    status: DocumentStatus
    created_at: datetime
    uploaded_by: UUID


class WorkspaceDocumentListResponse(BaseModel):
    """Paginated workspace document collection."""

    items: list[WorkspaceDocumentResponse]
    page: CursorPage


class DocumentProcessingResponse(BaseModel):
    """Document processing status projection."""

    document_id: UUID
    status: DocumentStatus
    stage: DocumentStage
    updated_at: datetime
    error: str | None = None
