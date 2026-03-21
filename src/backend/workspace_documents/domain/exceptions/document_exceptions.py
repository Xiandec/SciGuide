"""Workspace document domain exceptions."""

from __future__ import annotations

from uuid import UUID


class WorkspaceDocumentDomainError(Exception):
    """Base workspace document exception."""


class WorkspaceDocumentNotFoundError(WorkspaceDocumentDomainError):
    """Raised when a document does not exist in the workspace."""

    def __init__(self, document_id: UUID) -> None:
        super().__init__(f"Workspace document {document_id} was not found")


class WorkspaceDocumentAccessDeniedError(WorkspaceDocumentDomainError):
    """Raised when an actor cannot manage workspace documents."""

    def __init__(
        self,
        message: str = "Access to workspace documents is denied",
    ) -> None:
        super().__init__(message)


class WorkspaceDocumentStorageError(WorkspaceDocumentDomainError):
    """Raised when file storage operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class WorkspaceDocumentDispatchError(WorkspaceDocumentDomainError):
    """Raised when background indexing cannot be enqueued."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
