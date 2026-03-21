"""Background document indexing dispatcher contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class WorkspaceDocumentIndexingDispatcher(ABC):
    """Dispatch workspace document indexing jobs."""

    @abstractmethod
    async def enqueue(
        self,
        *,
        workspace_id: UUID,
        document_id: UUID,
    ) -> None:
        """Enqueue a background indexing task."""
