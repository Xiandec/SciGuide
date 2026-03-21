"""Workspace documents task dispatch adapters."""

from workspace_documents.infrastructure.dispatch.celery_document_indexing_dispatcher import (  # noqa: E501
    CeleryWorkspaceDocumentIndexingDispatcher,
)

__all__ = ["CeleryWorkspaceDocumentIndexingDispatcher"]
