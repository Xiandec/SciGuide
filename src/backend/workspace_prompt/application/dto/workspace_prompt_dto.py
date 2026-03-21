"""Workspace prompt DTOs used by the application layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from workspace_prompt.domain.entities.workspace_prompt import WorkspacePrompt


@dataclass(slots=True)
class WorkspacePromptDTO:
    """Workspace prompt payload returned to presentation."""

    workspace_id: UUID
    content: str
    updated_at: datetime
    updated_by: UUID

    @classmethod
    def from_entity(cls, prompt: WorkspacePrompt) -> "WorkspacePromptDTO":
        """Build DTO from a workspace prompt entity."""
        return cls(
            workspace_id=prompt.workspace_id,
            content=prompt.content,
            updated_at=prompt.updated_at,
            updated_by=prompt.updated_by,
        )
