"""Use case for loading a workspace document."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)
from workspace_documents.application.dto.document_dto import (
    WorkspaceDocumentDTO,
)
from workspace_documents.application.use_cases._workspace_access import (
    get_workspace_access_or_raise,
)
from workspace_documents.domain.exceptions.document_exceptions import (
    WorkspaceDocumentNotFoundError,
)
from workspace_documents.domain.repositories.workspace_document_repository import (  # noqa: E501
    WorkspaceDocumentRepository,
)


@dataclass(slots=True)
class GetWorkspaceDocumentRequest:
    """Get workspace document request payload."""

    workspace_id: UUID
    document_id: UUID
    actor_user_id: UUID


class GetWorkspaceDocument:
    """Load a document if the actor can access the workspace."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        document_repository: WorkspaceDocumentRepository,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._document_repository = document_repository

    async def execute(
        self,
        request: GetWorkspaceDocumentRequest,
    ) -> WorkspaceDocumentDTO:
        """Return document metadata or raise a not-found error."""
        await get_workspace_access_or_raise(
            workspace_repository=self._workspace_repository,
            workspace_id=request.workspace_id,
            user_id=request.actor_user_id,
        )
        document = await self._document_repository.get_by_id(
            workspace_id=request.workspace_id,
            document_id=request.document_id,
        )
        if document is None:
            raise WorkspaceDocumentNotFoundError(request.document_id)

        return WorkspaceDocumentDTO.from_entity(document)
