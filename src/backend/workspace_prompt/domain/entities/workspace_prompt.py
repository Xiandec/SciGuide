"""Workspace prompt domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class WorkspacePrompt:
    """System prompt bound to a single workspace."""

    workspace_id: UUID
    content: str
    created_at: datetime
    updated_at: datetime
    updated_by: UUID

    def __post_init__(self) -> None:
        """Normalize and validate prompt content."""
        self.content = self.content.strip()
        if not self.content:
            raise ValueError("Workspace prompt content cannot be empty")


@dataclass(slots=True)
class WorkspacePromptAccess:
    """Workspace prompt projection enriched with permissions."""

    prompt: WorkspacePrompt
    can_manage: bool
