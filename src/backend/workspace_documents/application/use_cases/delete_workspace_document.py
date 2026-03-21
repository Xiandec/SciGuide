"""Use case for deleting a workspace document."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)
from workspace_documents.application.use_cases._workspace_access import (
    ensure_workspace_admin,
)
from workspace_documents.application.use_cases._workspace_access import (
    get_workspace_access_or_raise,
)
from workspace_documents.domain.exceptions.document_exceptions import (
    WorkspaceDocumentNotFoundError,
)
from workspace_documents.domain.repositories.document_storage import (
    DocumentStorage,
)
from workspace_documents.domain.repositories.workspace_document_repository import (  # noqa: E501
    WorkspaceDocumentRepository,
)


@dataclass(slots=True)
class DeleteWorkspaceDocumentRequest:
    """Delete workspace document request payload."""

    workspace_id: UUID
    document_id: UUID
    actor_user_id: UUID


class DeleteWorkspaceDocument:
    """Delete document metadata and its stored file."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        document_repository: WorkspaceDocumentRepository,
        document_storage: DocumentStorage,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._document_repository = document_repository
        self._document_storage = document_storage

    async def execute(self, request: DeleteWorkspaceDocumentRequest) -> None:
        """Delete a document when the actor manages the workspace."""
        workspace_access = await get_workspace_access_or_raise(
            workspace_repository=self._workspace_repository,
            workspace_id=request.workspace_id,
            user_id=request.actor_user_id,
        )
        ensure_workspace_admin(workspace_access)

        deleted_document = await self._document_repository.delete_by_id(
            workspace_id=request.workspace_id,
            document_id=request.document_id,
        )
        if deleted_document is None:
            raise WorkspaceDocumentNotFoundError(request.document_id)

        await self._delete_stored_file(deleted_document.storage_key)

    async def _delete_stored_file(self, storage_key: str) -> None:
        """Best-effort file cleanup after metadata deletion."""
        try:
            await self._document_storage.delete(storage_key=storage_key)
        except OSError:
            return
