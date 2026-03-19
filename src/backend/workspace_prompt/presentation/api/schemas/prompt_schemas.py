"""Schemas for mock workspace prompt API."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkspacePromptResponse(BaseModel):
    """Workspace prompt projection."""

    workspace_id: UUID
    content: str = Field(..., min_length=1, max_length=20000)
    updated_at: datetime
    updated_by: UUID


class UpdateWorkspacePromptRequest(BaseModel):
    """Request payload for updating workspace prompt."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": (
                    "You are a scientific assistant specialized in "
                    "graph-guided retrieval."
                ),
            },
        },
    )

    content: str = Field(..., min_length=1, max_length=20000)
