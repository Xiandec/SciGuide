"""Workspace document domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from uuid import UUID


class DocumentStatus(str, Enum):
    """Allowed workspace document statuses."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class DocumentStage(str, Enum):
    """Allowed workspace document processing stages."""

    UPLOADED = "uploaded"
    TEXT_EXTRACTION = "text_extraction"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    GRAPH_UPDATE = "graph_update"
    COMPLETED = "completed"


@dataclass(slots=True)
class WorkspaceDocument:
    """Document metadata isolated inside a single workspace."""

    id: UUID
    workspace_id: UUID
    filename: str
    storage_key: str
    content_type: str
    size_bytes: int
    status: DocumentStatus
    processing_stage: DocumentStage
    processing_error: str | None
    uploaded_by: UUID
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Normalize and validate document state."""
        self.filename = Path(self.filename).name.strip()
        self.storage_key = self.storage_key.strip()
        self.content_type = self.content_type.strip()

        if self.processing_error is not None:
            self.processing_error = self.processing_error.strip() or None

        if not self.filename:
            raise ValueError("Document filename cannot be empty")
        if not self.storage_key:
            raise ValueError("Document storage key cannot be empty")
        if not self.content_type:
            raise ValueError("Document content type cannot be empty")
        if self.size_bytes < 0:
            raise ValueError("Document size cannot be negative")

        if self.status == DocumentStatus.UPLOADED:
            if self.processing_stage != DocumentStage.UPLOADED:
                raise ValueError(
                    "Uploaded document must use uploaded processing stage",
                )
        elif self.status == DocumentStatus.PROCESSING:
            if self.processing_stage not in {
                DocumentStage.TEXT_EXTRACTION,
                DocumentStage.CHUNKING,
                DocumentStage.EMBEDDING,
                DocumentStage.GRAPH_UPDATE,
            }:
                raise ValueError(
                    "Processing document must use active processing stage",
                )
        elif self.status == DocumentStatus.PROCESSED:
            if self.processing_stage != DocumentStage.COMPLETED:
                raise ValueError(
                    "Processed document must use completed stage",
                )
        elif self.processing_error is None:
            raise ValueError("Failed document must include processing error")
