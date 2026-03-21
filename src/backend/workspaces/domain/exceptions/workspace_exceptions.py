"""Workspace domain exceptions."""

from __future__ import annotations

from uuid import UUID


class WorkspaceDomainError(Exception):
    """Base workspace domain exception."""


class WorkspaceNotFoundError(WorkspaceDomainError):
    """Raised when a workspace cannot be found or accessed."""

    def __init__(self, workspace_id: UUID) -> None:
        super().__init__(f"Workspace {workspace_id} was not found")


class WorkspaceAccessDeniedError(WorkspaceDomainError):
    """Raised when a user cannot perform an operation."""

    def __init__(self, message: str = "Access to workspace is denied") -> None:
        super().__init__(message)


class WorkspaceLifecycleError(WorkspaceDomainError):
    """Raised when external workspace resources cannot be reconciled."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
