"""Developer-facing entrypoint for the SciGuide library."""

from __future__ import annotations

from pathlib import Path
from threading import Lock

from ..application.dto import RunChunkingRequest, RunSearchRequest
from ..application.use_cases import RunChunking, RunSearch
from ..domain.entities import ChunkingReport, SearchReport, SourceDocument
from ..domain.services import WeightedScoreCombiner
from ..infrastructure.embeddings import HuggingFaceEmbeddingService
from ..infrastructure.persistence import (
    Neo4jGraphRepository,
    QdrantVectorRepository,
)
from ..infrastructure.processing import (
    DeterministicEntityExtractor,
    LangChainTextChunker,
)


class ChunkingPipeline:
    """Presentation facade for document indexing."""

    def __init__(self, use_case: RunChunking) -> None:
        self._use_case = use_case

    def run(self, documents: list[SourceDocument]) -> ChunkingReport:
        """Index documents in vector and graph stores."""
        return self._use_case.execute(
            RunChunkingRequest(documents=documents)
        )


class SearchPipeline:
    """Presentation facade for retrieval."""

    def __init__(
        self,
        use_case: RunSearch,
        default_limit: int,
        default_candidate_limit: int,
    ) -> None:
        self._use_case = use_case
        self._default_limit = default_limit
        self._default_candidate_limit = default_candidate_limit

    def run(
        self,
        query: str,
        *,
        limit: int | None = None,
        candidate_limit: int | None = None,
    ) -> SearchReport:
        """Run hybrid retrieval for a query."""
        resolved_limit = max(limit or self._default_limit, 5)
        resolved_candidate_limit = max(
            candidate_limit or self._default_candidate_limit,
            resolved_limit,
        )
        return self._use_case.execute(
            RunSearchRequest(
                query=query,
                limit=resolved_limit,
                candidate_limit=resolved_candidate_limit,
            )
        )


class PipelineManager:
    """Main developer-facing entrypoint for the SciGuide library."""

    _runtime_lock = Lock()
    _entity_extractor = DeterministicEntityExtractor()
    _text_chunkers: dict[tuple[int, int], LangChainTextChunker] = {}
    _embedding_services: dict[
        tuple[str, str, str | None],
        HuggingFaceEmbeddingService,
    ] = {}
    _ensured_graph_schemas: set[tuple[str, str, str]] = set()

    def __init__(
        self,
        qdrant_url: str,
        qdrant_collection_name: str,
        neo4j_uri: str,
        neo4j_username: str,
        neo4j_password: str,
        embedding_model_name: str,
        reranker_model_name: str,
        model_cache_dir: str | Path,
        *,
        graph_namespace: str | None = None,
        qdrant_api_key: str | None = None,
        qdrant_prefer_grpc: bool = False,
        neo4j_database: str = "neo4j",
        huggingface_token: str | None = None,
        chunk_size: int = 1200,
        chunk_overlap: int = 200,
        search_limit: int = 5,
        search_candidate_limit: int = 20,
        vector_weight: float = 0.45,
        graph_weight: float = 0.20,
        rerank_weight: float = 0.35,
        request_timeout: float = 60.0,
    ) -> None:
        cache_dir = Path(model_cache_dir)
        resolved_graph_namespace = graph_namespace or qdrant_collection_name

        self._entity_extractor = self.__class__._entity_extractor
        self._text_chunker = self._get_or_create_text_chunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self._embedding_service = self._get_or_create_embedding_service(
            model_name=embedding_model_name,
            cache_dir=cache_dir,
            token=huggingface_token,
        )
        self._vector_repository = QdrantVectorRepository(
            url=qdrant_url,
            collection_name=qdrant_collection_name,
            api_key=qdrant_api_key,
            prefer_grpc=qdrant_prefer_grpc,
            timeout=request_timeout,
        )
        self._graph_repository = Neo4jGraphRepository(
            uri=neo4j_uri,
            username=neo4j_username,
            password=neo4j_password,
            database=neo4j_database,
            namespace=resolved_graph_namespace,
        )
        self._score_combiner = WeightedScoreCombiner(
            vector_weight=vector_weight,
            graph_weight=graph_weight,
            rerank_weight=rerank_weight,
        )

        # Warm up infrastructure eagerly so the service does not re-download
        # or initialize critical dependencies on the first user request.
        self._vector_repository.ensure_collection(
            self._embedding_service.vector_size
        )
        self._ensure_graph_schema_once(
            uri=neo4j_uri,
            username=neo4j_username,
            database=neo4j_database,
        )

        self._chunking_use_case = RunChunking(
            text_chunker=self._text_chunker,
            entity_extractor=self._entity_extractor,
            embedding_service=self._embedding_service,
            vector_repository=self._vector_repository,
            graph_repository=self._graph_repository,
            collection_name=qdrant_collection_name,
            graph_namespace=resolved_graph_namespace,
        )
        self._search_use_case = RunSearch(
            entity_extractor=self._entity_extractor,
            embedding_service=self._embedding_service,
            vector_repository=self._vector_repository,
            graph_repository=self._graph_repository,
            score_combiner=self._score_combiner,
        )

        self.chunking = ChunkingPipeline(self._chunking_use_case)
        self.search = SearchPipeline(
            self._search_use_case,
            default_limit=search_limit,
            default_candidate_limit=search_candidate_limit,
        )

    def close(self) -> None:
        """Release infrastructure resources."""
        self._graph_repository.close()
        self._vector_repository.close()

    def __enter__(self) -> "PipelineManager":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    @classmethod
    def _get_or_create_text_chunker(
        cls,
        *,
        chunk_size: int,
        chunk_overlap: int,
    ) -> LangChainTextChunker:
        key = (chunk_size, chunk_overlap)
        with cls._runtime_lock:
            existing = cls._text_chunkers.get(key)
            if existing is not None:
                return existing

            chunker = LangChainTextChunker(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            cls._text_chunkers[key] = chunker
            return chunker

    @classmethod
    def _get_or_create_embedding_service(
        cls,
        *,
        model_name: str,
        cache_dir: Path,
        token: str | None,
    ) -> HuggingFaceEmbeddingService:
        key = (model_name, str(cache_dir.resolve()), token)
        with cls._runtime_lock:
            existing = cls._embedding_services.get(key)
            if existing is not None:
                return existing

            service = HuggingFaceEmbeddingService(
                model_name=model_name,
                cache_dir=cache_dir,
                token=token,
            )
            cls._embedding_services[key] = service
            return service

    def _ensure_graph_schema_once(
        self,
        *,
        uri: str,
        username: str,
        database: str,
    ) -> None:
        key = (uri, username, database)
        with self.__class__._runtime_lock:
            if key in self.__class__._ensured_graph_schemas:
                return

        self._graph_repository.ensure_schema()

        with self.__class__._runtime_lock:
            self.__class__._ensured_graph_schemas.add(key)
