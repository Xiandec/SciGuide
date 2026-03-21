"""Workspace document repository contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from workspace_documents.domain.entities.workspace_document import (
    WorkspaceDocument,
)


class WorkspaceDocumentRepository(ABC):
    """Abstract persistence contract for workspace documents."""

    @abstractmethod
    async def list_by_workspace(
        self,
        *,
        workspace_id: UUID,
        limit: int,
        cursor: str | None,
    ) -> tuple[list[WorkspaceDocument], str | None, bool]:
        """List documents for a workspace."""

    @abstractmethod
    async def create(
        self,
        document: WorkspaceDocument,
    ) -> WorkspaceDocument:
        """Persist a workspace document."""

    @abstractmethod
    async def get_by_id(
        self,
        *,
        workspace_id: UUID,
        document_id: UUID,
    ) -> WorkspaceDocument | None:
        """Load a document by id within a workspace."""

    @abstractmethod
    async def delete_by_id(
        self,
        *,
        workspace_id: UUID,
        document_id: UUID,
    ) -> WorkspaceDocument | None:
        """Delete a document and return its previous metadata."""

    @abstractmethod
    async def update_processing_state(
        self,
        *,
        workspace_id: UUID,
        document_id: UUID,
        status: str,
        processing_stage: str,
        processing_error: str | None,
    ) -> WorkspaceDocument | None:
        """Update document processing state and return fresh metadata."""
