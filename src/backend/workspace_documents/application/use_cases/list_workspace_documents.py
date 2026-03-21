"""Use case for listing workspace documents."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)
from workspace_documents.application.dto.document_dto import (
    WorkspaceDocumentDTO,
)
from workspace_documents.application.dto.document_dto import (
    WorkspaceDocumentListDTO,
)
from workspace_documents.application.use_cases._workspace_access import (
    get_workspace_access_or_raise,
)
from workspace_documents.domain.repositories.workspace_document_repository import (  # noqa: E501
    WorkspaceDocumentRepository,
)


@dataclass(slots=True)
class ListWorkspaceDocumentsRequest:
    """List workspace documents request payload."""

    workspace_id: UUID
    actor_user_id: UUID
    limit: int
    cursor: str | None


class ListWorkspaceDocuments:
    """List documents available inside an accessible workspace."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        document_repository: WorkspaceDocumentRepository,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._document_repository = document_repository

    async def execute(
        self,
        request: ListWorkspaceDocumentsRequest,
    ) -> WorkspaceDocumentListDTO:
        """Return paginated documents for an accessible workspace."""
        await get_workspace_access_or_raise(
            workspace_repository=self._workspace_repository,
            workspace_id=request.workspace_id,
            user_id=request.actor_user_id,
        )
        items, next_cursor, has_more = (
            await self._document_repository.list_by_workspace(
                workspace_id=request.workspace_id,
                limit=request.limit,
                cursor=request.cursor,
            )
        )
        return WorkspaceDocumentListDTO(
            items=[WorkspaceDocumentDTO.from_entity(item) for item in items],
            next_cursor=next_cursor,
            has_more=has_more,
        )
