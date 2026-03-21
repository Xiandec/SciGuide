"""Use case for listing accessible workspaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from workspaces.application.dto.workspace_dto import WorkspaceDTO
from workspaces.application.dto.workspace_dto import WorkspaceListDTO
from workspaces.domain.entities.workspace import WorkspaceType
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)


@dataclass(slots=True)
class ListWorkspacesRequest:
    """List request payload."""

    user_id: UUID
    workspace_type: WorkspaceType | None
    limit: int
    cursor: str | None
    sort: Literal["-created_at", "created_at"]


class ListWorkspaces:
    """List workspaces accessible for the current user."""

    def __init__(self, workspace_repository: WorkspaceRepository) -> None:
        self._workspace_repository = workspace_repository

    async def execute(
        self,
        request: ListWorkspacesRequest,
    ) -> WorkspaceListDTO:
        """Return paginated accessible workspaces."""
        items, next_cursor, has_more = (
            await self._workspace_repository.list_accessible(
                user_id=request.user_id,
                workspace_type=request.workspace_type,
                limit=request.limit,
                cursor=request.cursor,
                sort_desc=request.sort.startswith("-"),
            )
        )

        return WorkspaceListDTO(
            items=[WorkspaceDTO.from_access(item) for item in items],
            next_cursor=next_cursor,
            has_more=has_more,
        )
