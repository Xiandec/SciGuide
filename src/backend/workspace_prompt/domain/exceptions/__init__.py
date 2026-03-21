"""Workspace prompt domain exceptions."""

from workspace_prompt.domain.exceptions.workspace_prompt_exceptions import (
    WorkspacePromptAccessDeniedError,
)
from workspace_prompt.domain.exceptions.workspace_prompt_exceptions import (
    WorkspacePromptDomainError,
)
from workspace_prompt.domain.exceptions.workspace_prompt_exceptions import (
    WorkspacePromptNotFoundError,
)

__all__ = [
    "WorkspacePromptAccessDeniedError",
    "WorkspacePromptDomainError",
    "WorkspacePromptNotFoundError",
]
