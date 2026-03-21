"""Use case for indexing a stored workspace document."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

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
    WorkspaceDocumentNotFoundError,
)
from workspace_documents.domain.repositories.document_storage import (
    DocumentStorage,
)
from workspace_documents.domain.repositories.workspace_document_repository import (  # noqa: E501
    WorkspaceDocumentRepository,
)
from workspace_documents.domain.services.workspace_document_indexer import (
    WorkspaceDocumentIndexer,
)


@dataclass(slots=True)
class ProcessWorkspaceDocumentRequest:
    """Process workspace document request payload."""

    workspace_id: UUID
    document_id: UUID


class ProcessWorkspaceDocument:
    """Read a stored document and index it into retrieval stores."""

    def __init__(
        self,
        document_repository: WorkspaceDocumentRepository,
        document_storage: DocumentStorage,
        document_indexer: WorkspaceDocumentIndexer,
    ) -> None:
        self._document_repository = document_repository
        self._document_storage = document_storage
        self._document_indexer = document_indexer

    async def execute(self, request: ProcessWorkspaceDocumentRequest) -> None:
        """Process one workspace document and update status transitions."""
        document = await self._document_repository.get_by_id(
            workspace_id=request.workspace_id,
            document_id=request.document_id,
        )
        if document is None:
            raise WorkspaceDocumentNotFoundError(request.document_id)

        if document.status == DocumentStatus.PROCESSED:
            return

        current_stage = DocumentStage.UPLOADED
        try:
            current_stage = DocumentStage.TEXT_EXTRACTION
            document = await self._update_state(
                document=document,
                status=DocumentStatus.PROCESSING,
                stage=current_stage,
                error=None,
            )
            content_bytes = await self._document_storage.read_bytes(
                storage_key=document.storage_key,
            )

            current_stage = DocumentStage.CHUNKING
            document = await self._update_state(
                document=document,
                status=DocumentStatus.PROCESSING,
                stage=current_stage,
                error=None,
            )
            await self._document_indexer.index(
                document=document,
                content_bytes=content_bytes,
            )

            await self._update_state(
                document=document,
                status=DocumentStatus.PROCESSED,
                stage=DocumentStage.COMPLETED,
                error=None,
            )
        except Exception as exc:
            await self._document_repository.update_processing_state(
                workspace_id=request.workspace_id,
                document_id=request.document_id,
                status=DocumentStatus.FAILED.value,
                processing_stage=current_stage.value,
                processing_error=self._build_error_message(exc),
            )
            raise

    async def _update_state(
        self,
        *,
        document: WorkspaceDocument,
        status: DocumentStatus,
        stage: DocumentStage,
        error: str | None,
    ) -> WorkspaceDocument:
        """Persist state transition and return the updated document."""
        updated_document = await self._document_repository.update_processing_state(
            workspace_id=document.workspace_id,
            document_id=document.id,
            status=status.value,
            processing_stage=stage.value,
            processing_error=error,
        )
        if updated_document is None:
            raise WorkspaceDocumentNotFoundError(document.id)
        return updated_document

    @staticmethod
    def _build_error_message(error: Exception) -> str:
        """Normalize an exception for persistent processing error storage."""
        message = str(error).strip()
        if message:
            return message[:4000]
        return error.__class__.__name__
