"""Workspace documents domain exceptions."""

from workspace_documents.domain.exceptions.document_exceptions import (
    WorkspaceDocumentAccessDeniedError,
)
from workspace_documents.domain.exceptions.document_exceptions import (
    WorkspaceDocumentDomainError,
)
from workspace_documents.domain.exceptions.document_exceptions import (
    WorkspaceDocumentDispatchError,
)
from workspace_documents.domain.exceptions.document_exceptions import (
    WorkspaceDocumentNotFoundError,
)
from workspace_documents.domain.exceptions.document_exceptions import (
    WorkspaceDocumentStorageError,
)

__all__ = [
    "WorkspaceDocumentAccessDeniedError",
    "WorkspaceDocumentDomainError",
    "WorkspaceDocumentDispatchError",
    "WorkspaceDocumentNotFoundError",
    "WorkspaceDocumentStorageError",
]
