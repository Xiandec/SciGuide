"""Workspace document DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from workspace_documents.domain.entities.workspace_document import (
    DocumentStage,
)
from workspace_documents.domain.entities.workspace_document import (
    DocumentStatus,
)
from workspace_documents.domain.entities.workspace_document import (
    WorkspaceDocument,
)


@dataclass(slots=True)
class WorkspaceDocumentDTO:
    """Document projection returned to presentation."""

    id: UUID
    workspace_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    status: DocumentStatus
    created_at: datetime
    uploaded_by: UUID

    @classmethod
    def from_entity(
        cls,
        document: WorkspaceDocument,
    ) -> "WorkspaceDocumentDTO":
        """Map a domain entity into API-facing DTO."""
        return cls(
            id=document.id,
            workspace_id=document.workspace_id,
            filename=document.filename,
            content_type=document.content_type,
            size_bytes=document.size_bytes,
            status=document.status,
            created_at=document.created_at,
            uploaded_by=document.uploaded_by,
        )


@dataclass(slots=True)
class WorkspaceDocumentListDTO:
    """Paginated document collection."""

    items: list[WorkspaceDocumentDTO]
    next_cursor: str | None
    has_more: bool


@dataclass(slots=True)
class DocumentProcessingDTO:
    """Document processing state projection."""

    document_id: UUID
    status: DocumentStatus
    stage: DocumentStage
    updated_at: datetime
    error: str | None

    @classmethod
    def from_entity(
        cls,
        document: WorkspaceDocument,
    ) -> "DocumentProcessingDTO":
        """Map a document entity into processing projection."""
        return cls(
            document_id=document.id,
            status=document.status,
            stage=document.processing_stage,
            updated_at=document.updated_at,
            error=document.processing_error,
        )
