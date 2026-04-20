# Ключевые листинги исходного кода

В приложении приведены расширенные фрагменты исходного кода, которые показывают организацию retrieval-контура и фоновую обработку документов.

```python {#app-lst-run-chunking caption="Сценарий RunChunking: оркестрация chunking, embedding и сохранения"}
class RunChunking:
    """Orchestrates chunking, embedding, and persistence."""

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
                entities=tuple(self._entity_extractor.extract(chunk.text)),
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
```

```python {#app-lst-pipeline-manager caption="Класс PipelineManager: сборка фасадов chunking и search"}
class PipelineManager:
    """Main developer-facing entrypoint for the SciGuide library."""

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
        ...
        self.chunking = ChunkingPipeline(self._chunking_use_case)
        self.search = SearchPipeline(
            self._search_use_case,
            default_limit=search_limit,
            default_candidate_limit=search_candidate_limit,
        )
```

```python {#app-lst-celery-app caption="Конфигурация Celery для фоновой индексации документов"}
celery_app = Celery(
    "sciguide",
    broker=_build_redis_url(),
    backend=_build_redis_url(),
    include=["workspace_documents.infrastructure.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_default_queue="workspace-document-indexing",
    task_track_started=True,
    timezone="UTC",
    enable_utc=True,
)
```
