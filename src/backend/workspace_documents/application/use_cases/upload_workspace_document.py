"""Use case for uploading a workspace document."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO
from uuid import UUID, uuid4

from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)
from workspace_documents.application.dto.document_dto import (
    WorkspaceDocumentDTO,
)
from workspace_documents.application.use_cases._workspace_access import (
    ensure_workspace_admin,
)
from workspace_documents.application.use_cases._workspace_access import (
    get_workspace_access_or_raise,
)
from workspace_documents.domain.entities.workspace_document import (
    DocumentStage,
)
from workspace_documents.domain.entities.workspace_document import (
    DocumentStatus,
)
from workspace_documents.domain.entities.workspace_document import (
    WorkspaceDocument,
)
from workspace_documents.domain.exceptions.document_exceptions import (
    WorkspaceDocumentStorageError,
)
from workspace_documents.domain.repositories.document_storage import (
    DocumentStorage,
)
from workspace_documents.domain.repositories.workspace_document_repository import (  # noqa: E501
    WorkspaceDocumentRepository,
)


@dataclass(slots=True)
class UploadWorkspaceDocumentRequest:
    """Upload workspace document request payload."""

    workspace_id: UUID
    actor_user_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    file_stream: BinaryIO


class UploadWorkspaceDocument:
    """Upload a document into workspace storage and metadata store."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        document_repository: WorkspaceDocumentRepository,
        document_storage: DocumentStorage,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._document_repository = document_repository
        self._document_storage = document_storage

    async def execute(
        self,
        request: UploadWorkspaceDocumentRequest,
    ) -> WorkspaceDocumentDTO:
        """Persist document content and create document metadata."""
        workspace_access = await get_workspace_access_or_raise(
            workspace_repository=self._workspace_repository,
            workspace_id=request.workspace_id,
            user_id=request.actor_user_id,
        )
        ensure_workspace_admin(workspace_access)

        filename = Path(request.filename).name.strip() or "document.bin"
        content_type = request.content_type.strip() or "application/octet-stream"
        timestamp = datetime.now(timezone.utc)
        document_id = uuid4()

        try:
            storage_key = await self._document_storage.save(
                workspace_id=request.workspace_id,
                document_id=document_id,
                filename=filename,
                source=request.file_stream,
                size_bytes=request.size_bytes,
                content_type=content_type,
            )
        except OSError as exc:
            raise WorkspaceDocumentStorageError(
                "Failed to store workspace document content",
            ) from exc

        document = WorkspaceDocument(
            id=document_id,
            workspace_id=request.workspace_id,
            filename=filename,
            storage_key=storage_key,
            content_type=content_type,
            size_bytes=request.size_bytes,
            status=DocumentStatus.UPLOADED,
            processing_stage=DocumentStage.UPLOADED,
            processing_error=None,
            uploaded_by=request.actor_user_id,
            created_at=timestamp,
            updated_at=timestamp,
        )

        try:
            created_document = await self._document_repository.create(document)
        except Exception:
            await self._delete_stored_file(storage_key)
            raise

        return WorkspaceDocumentDTO.from_entity(created_document)

    async def _delete_stored_file(self, storage_key: str) -> None:
        """Best-effort cleanup for failed metadata creation."""
        try:
            await self._document_storage.delete(storage_key=storage_key)
        except OSError:
            return
