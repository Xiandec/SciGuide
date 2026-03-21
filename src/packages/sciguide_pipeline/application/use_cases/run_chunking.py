"""Use case for document chunking and indexing."""

from __future__ import annotations

from dataclasses import replace

from ..dto import RunChunkingRequest
from ...domain.entities import ChunkingReport
from ...domain.repositories import GraphRepository, VectorRepository
from ...domain.services import ConceptExtractor, EmbeddingService, TextChunker


class RunChunking:
    """Orchestrates chunking, embedding, and persistence."""

    def __init__(
        self,
        text_chunker: TextChunker,
        concept_extractor: ConceptExtractor,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository,
        graph_repository: GraphRepository,
        collection_name: str,
        graph_namespace: str,
    ) -> None:
        self._text_chunker = text_chunker
        self._concept_extractor = concept_extractor
        self._embedding_service = embedding_service
        self._vector_repository = vector_repository
        self._graph_repository = graph_repository
        self._collection_name = collection_name
        self._graph_namespace = graph_namespace

    def execute(self, request: RunChunkingRequest) -> ChunkingReport:
        """Execute the end-to-end chunking workflow."""
        chunks = self._text_chunker.chunk_documents(request.documents)
        if not chunks:
            return ChunkingReport(
                documents_processed=len(request.documents),
                chunks_created=0,
                collection_name=self._collection_name,
                graph_namespace=self._graph_namespace,
            )

        enriched_chunks = [
            replace(
                chunk,
                concepts=tuple(self._concept_extractor.extract(chunk.text)),
            )
            for chunk in chunks
        ]

        embeddings = self._embedding_service.embed_documents(
            [chunk.text for chunk in enriched_chunks]
        )

        self._vector_repository.ensure_collection(
            self._embedding_service.vector_size
        )
        self._vector_repository.upsert_chunks(enriched_chunks, embeddings)
        self._graph_repository.ensure_schema()
        self._graph_repository.upsert_chunks(enriched_chunks)

        return ChunkingReport(
            documents_processed=len(request.documents),
            chunks_created=len(enriched_chunks),
            collection_name=self._collection_name,
            graph_namespace=self._graph_namespace,
        )
