"""Workspace document indexing service contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from workspace_documents.domain.entities.workspace_document import (
    WorkspaceDocument,
)


class WorkspaceDocumentIndexer(ABC):
    """Index workspace documents into retrieval infrastructure."""

    @abstractmethod
    async def index(
        self,
        *,
        document: WorkspaceDocument,
        content_bytes: bytes,
    ) -> None:
        """Index a stored workspace document."""
