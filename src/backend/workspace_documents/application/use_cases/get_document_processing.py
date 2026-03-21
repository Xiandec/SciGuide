"""Use case for loading document processing status."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)
from workspace_documents.application.dto.document_dto import (
    DocumentProcessingDTO,
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
class GetDocumentProcessingRequest:
    """Get document processing request payload."""

    workspace_id: UUID
    document_id: UUID
    actor_user_id: UUID


class GetDocumentProcessing:
    """Load processing status for a workspace document."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        document_repository: WorkspaceDocumentRepository,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._document_repository = document_repository

    async def execute(
        self,
        request: GetDocumentProcessingRequest,
    ) -> DocumentProcessingDTO:
        """Return processing state for a document in accessible workspace."""
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

        return DocumentProcessingDTO.from_entity(document)
