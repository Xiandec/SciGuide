"""Workspace prompt domain exceptions."""

from __future__ import annotations

from uuid import UUID


class WorkspacePromptDomainError(Exception):
    """Base workspace prompt domain exception."""


class WorkspacePromptNotFoundError(WorkspacePromptDomainError):
    """Raised when a workspace prompt cannot be found or accessed."""

    def __init__(self, workspace_id: UUID) -> None:
        super().__init__(
            f"Workspace prompt for workspace {workspace_id} was not found",
        )


class WorkspacePromptAccessDeniedError(WorkspacePromptDomainError):
    """Raised when a user cannot manage the workspace prompt."""

    def __init__(
        self,
        message: str = "Access to workspace prompt is denied",
    ) -> None:
        super().__init__(message)
