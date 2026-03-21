"""PipelineManager-backed document indexer."""

from __future__ import annotations

from sciguide_pipeline import PipelineManager
from sciguide_pipeline import SourceDocument

from config import settings
from workspace_documents.domain.entities.workspace_document import (
    WorkspaceDocument,
)
from workspace_documents.domain.services.workspace_document_indexer import (
    WorkspaceDocumentIndexer,
)


class PipelineManagerWorkspaceDocumentIndexer(WorkspaceDocumentIndexer):
    """Index documents with the shared SciGuide pipeline library."""

    async def index(
        self,
        *,
        document: WorkspaceDocument,
        content_bytes: bytes,
    ) -> None:
        """Run chunking/indexing for one workspace document."""
        collection_name = (
            f"{settings.qdrant_collection_prefix}{document.workspace_id.hex}"
        )

        source_document = SourceDocument(
            content=content_bytes,
            document_id=str(document.id),
            source_name=document.filename,
            metadata={
                "workspace_id": str(document.workspace_id),
                "workspace_document_id": str(document.id),
                "filename": document.filename,
                "content_type": document.content_type,
                "uploaded_by": str(document.uploaded_by),
            },
        )

        with PipelineManager(
            qdrant_url=settings.qdrant_url,
            qdrant_collection_name=collection_name,
            neo4j_uri=settings.pipeline_neo4j_uri,
            neo4j_username=settings.neo4j_username,
            neo4j_password=settings.neo4j_password,
            embedding_model_name=settings.pipeline_embedding_model_name,
            reranker_model_name=settings.pipeline_reranker_model_name,
            model_cache_dir=settings.pipeline_model_cache_dir,
            graph_namespace=collection_name,
            qdrant_api_key=settings.qdrant_api_key,
            qdrant_prefer_grpc=settings.qdrant_prefer_grpc,
            neo4j_database=settings.neo4j_database,
            huggingface_token=settings.huggingface_token,
            chunk_size=settings.pipeline_chunk_size,
            chunk_overlap=settings.pipeline_chunk_overlap,
            request_timeout=settings.pipeline_request_timeout_seconds,
        ) as manager:
            manager.chunking.run([source_document])
