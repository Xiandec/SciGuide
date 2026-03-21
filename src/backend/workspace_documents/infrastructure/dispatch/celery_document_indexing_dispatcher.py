"""Celery-based dispatcher for workspace document indexing."""

from __future__ import annotations

from uuid import UUID

from celery_app import celery_app
from workspace_documents.domain.exceptions.document_exceptions import (
    WorkspaceDocumentDispatchError,
)
from workspace_documents.domain.services.workspace_document_indexing_dispatcher import (  # noqa: E501
    WorkspaceDocumentIndexingDispatcher,
)


class CeleryWorkspaceDocumentIndexingDispatcher(
    WorkspaceDocumentIndexingDispatcher
):
    """Enqueue document indexing work on a Celery queue."""

    task_name = "workspace_documents.process_document_indexing"

    async def enqueue(
        self,
        *,
        workspace_id: UUID,
        document_id: UUID,
    ) -> None:
        """Send a document indexing task to the background worker."""
        try:
            celery_app.send_task(
                self.task_name,
                kwargs={
                    "workspace_id": str(workspace_id),
                    "document_id": str(document_id),
                },
            )
        except Exception as exc:
            raise WorkspaceDocumentDispatchError(
                "Failed to enqueue document indexing task",
            ) from exc
