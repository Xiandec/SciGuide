"""Celery tasks for workspace document processing."""

from __future__ import annotations

import asyncio
from uuid import UUID

import asyncpg

from celery_app import celery_app
from config import settings
from sciguide_pipeline.domain.exceptions import MissingDependencyError
from sciguide_pipeline.domain.exceptions import PipelineInitializationError
from workspace_documents.application.use_cases.process_workspace_document import (  # noqa: E501
    ProcessWorkspaceDocument,
)
from workspace_documents.application.use_cases.process_workspace_document import (  # noqa: E501
    ProcessWorkspaceDocumentRequest,
)
from workspace_documents.infrastructure.indexing import (
    PipelineManagerWorkspaceDocumentIndexer,
)
from workspace_documents.infrastructure.persistence import (
    PostgresWorkspaceDocumentRepository,
)
from workspace_documents.infrastructure.storage import (
    MinioDocumentStorage,
)


@celery_app.task(
    name="workspace_documents.process_document_indexing",
    autoretry_for=(Exception,),
    dont_autoretry_for=(
        PipelineInitializationError,
        MissingDependencyError,
    ),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_document_indexing_task(
    workspace_id: str,
    document_id: str,
) -> None:
    """Celery entrypoint for workspace document indexing."""
    asyncio.run(
        _process_document_indexing(
            workspace_id=UUID(workspace_id),
            document_id=UUID(document_id),
        )
    )


async def _process_document_indexing(
    *,
    workspace_id: UUID,
    document_id: UUID,
) -> None:
    """Build dependencies and process one workspace document."""
    pool = await asyncpg.create_pool(
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        host=settings.db_host,
        port=settings.db_port,
    )
    try:
        use_case = ProcessWorkspaceDocument(
            document_repository=PostgresWorkspaceDocumentRepository(pool),
            document_storage=MinioDocumentStorage(
                endpoint=settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                bucket_name=settings.minio_bucket_name,
                secure=settings.minio_secure,
                region=settings.minio_region,
            ),
            document_indexer=PipelineManagerWorkspaceDocumentIndexer(),
        )
        await use_case.execute(
            ProcessWorkspaceDocumentRequest(
                workspace_id=workspace_id,
                document_id=document_id,
            )
        )
    finally:
        await pool.close()
