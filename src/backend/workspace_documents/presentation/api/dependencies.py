"""Dependency wiring for workspace documents use cases."""

from __future__ import annotations

from functools import lru_cache

from asyncpg import Pool
from fastapi import Depends

from auth.presentation.api.dependencies import get_db_pool
from config import settings
from workspace_documents.application.use_cases.delete_workspace_document import (  # noqa: E501
    DeleteWorkspaceDocument,
)
from workspace_documents.application.use_cases.get_document_processing import (
    GetDocumentProcessing,
)
from workspace_documents.application.use_cases.get_workspace_document import (
    GetWorkspaceDocument,
)
from workspace_documents.application.use_cases.list_workspace_documents import (  # noqa: E501
    ListWorkspaceDocuments,
)
from workspace_documents.application.use_cases.upload_workspace_document import (  # noqa: E501
    UploadWorkspaceDocument,
)
from workspace_documents.domain.repositories.document_storage import (
    DocumentStorage,
)
from workspace_documents.domain.repositories.workspace_document_repository import (  # noqa: E501
    WorkspaceDocumentRepository,
)
from workspace_documents.infrastructure.persistence import (
    PostgresWorkspaceDocumentRepository,
)
from workspace_documents.infrastructure.storage import (
    MinioDocumentStorage,
)
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)
from workspaces.presentation.api.dependencies import (
    get_workspace_repository,
)


def get_workspace_document_repository(
    pool: Pool = Depends(get_db_pool),
) -> WorkspaceDocumentRepository:
    """Build workspace document repository."""
    return PostgresWorkspaceDocumentRepository(pool)


@lru_cache(maxsize=1)
def get_document_storage() -> DocumentStorage:
    """Build workspace document storage adapter."""
    return MinioDocumentStorage(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket_name=settings.minio_bucket_name,
        secure=settings.minio_secure,
        region=settings.minio_region,
    )


def get_list_workspace_documents_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
    document_repository: WorkspaceDocumentRepository = Depends(
        get_workspace_document_repository,
    ),
) -> ListWorkspaceDocuments:
    """Build list workspace documents use case."""
    return ListWorkspaceDocuments(
        workspace_repository=workspace_repository,
        document_repository=document_repository,
    )


def get_upload_workspace_document_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
    document_repository: WorkspaceDocumentRepository = Depends(
        get_workspace_document_repository,
    ),
    document_storage: DocumentStorage = Depends(get_document_storage),
) -> UploadWorkspaceDocument:
    """Build upload workspace document use case."""
    return UploadWorkspaceDocument(
        workspace_repository=workspace_repository,
        document_repository=document_repository,
        document_storage=document_storage,
    )


def get_get_workspace_document_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
    document_repository: WorkspaceDocumentRepository = Depends(
        get_workspace_document_repository,
    ),
) -> GetWorkspaceDocument:
    """Build get workspace document use case."""
    return GetWorkspaceDocument(
        workspace_repository=workspace_repository,
        document_repository=document_repository,
    )


def get_delete_workspace_document_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
    document_repository: WorkspaceDocumentRepository = Depends(
        get_workspace_document_repository,
    ),
    document_storage: DocumentStorage = Depends(get_document_storage),
) -> DeleteWorkspaceDocument:
    """Build delete workspace document use case."""
    return DeleteWorkspaceDocument(
        workspace_repository=workspace_repository,
        document_repository=document_repository,
        document_storage=document_storage,
    )


def get_document_processing_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
    document_repository: WorkspaceDocumentRepository = Depends(
        get_workspace_document_repository,
    ),
) -> GetDocumentProcessing:
    """Build get document processing use case."""
    return GetDocumentProcessing(
        workspace_repository=workspace_repository,
        document_repository=document_repository,
    )
