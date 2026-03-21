"""Workspace documents repository contracts."""

from workspace_documents.domain.repositories.document_storage import (
    DocumentStorage,
)
from workspace_documents.domain.repositories.workspace_document_repository import (  # noqa: E501
    WorkspaceDocumentRepository,
)

__all__ = [
    "DocumentStorage",
    "WorkspaceDocumentRepository",
]
