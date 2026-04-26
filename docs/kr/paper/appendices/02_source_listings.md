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

```python {#app-lst-gnn-features caption="Формирование признаков пары для обучаемого reranking-слоя"}
def candidate_features(query_id: str, doc_id: str) -> list[float]:
    rank = baseline_rank_lookup[query_id].get(doc_id, CANDIDATES_PER_QUERY + 1)
    return [
        float(semantic_document_scores_by_query[query_id].get(doc_id, 0.0)),
        float(graph_document_scores_by_query[query_id].get(doc_id, 0.0)),
        float(baseline_document_scores_by_query[query_id].get(doc_id, 0.0)),
        1.0 / rank,
        1.0 - min(rank - 1, CANDIDATES_PER_QUERY) / CANDIDATES_PER_QUERY,
    ]


def model_rankings(model: nn.Module, query_ids: list[str], residual_alpha: float) -> dict[str, list[str]]:
    model.eval()
    rankings = {}
    with torch.no_grad():
        z = model.encode(data)
        for query_id in query_ids:
            doc_ids = candidates_by_query[query_id]
            pairs = torch.tensor(
                [(node_index[("query", query_id)], node_index[("document", doc_id)]) for doc_id in doc_ids],
                dtype=torch.long,
                device=device,
            ).t().contiguous()
            pair_features = candidate_feature_tensor(query_id, doc_ids)
            correction = normalize(model.decoder(z, pairs, pair_features).cpu().numpy().astype(np.float32))
            scores = candidate_baseline_scores(query_id, doc_ids) + residual_alpha * correction
            rankings[query_id] = [doc_id for _, doc_id in sorted(zip(scores, doc_ids), reverse=True)]
    return rankings
```

```python {#app-lst-gnn-models caption="Общий декодер и варианты графовых моделей"}
class LinkDecoder(nn.Module):
    def __init__(self, hidden_dim: int, dropout: float, feature_dim: int):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(hidden_dim * 4 + feature_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, z: torch.Tensor, pair_index: torch.Tensor, pair_features: torch.Tensor) -> torch.Tensor:
        q = z[pair_index[0]]
        d = z[pair_index[1]]
        graph_features = torch.cat([q, d, torch.abs(q - d), q * d], dim=-1)
        return self.mlp(torch.cat([graph_features, pair_features], dim=-1)).squeeze(-1)


class GraphSAGEModel(BaseReranker):
    def __init__(self, input_dim: int, hidden_dim: int, dropout: float):
        super().__init__(hidden_dim, dropout)
        self.conv1 = SAGEConv(input_dim, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, hidden_dim)


class GATModel(BaseReranker):
    def __init__(self, input_dim: int, hidden_dim: int, dropout: float):
        super().__init__(hidden_dim, dropout)
        self.conv1 = GATConv(input_dim, hidden_dim, heads=2, concat=False, dropout=dropout)
        self.conv2 = GATConv(hidden_dim, hidden_dim, heads=1, concat=False, dropout=dropout)


class RGCNModel(BaseReranker):
    def __init__(self, input_dim: int, hidden_dim: int, dropout: float, num_relations: int):
        super().__init__(hidden_dim, dropout)
        self.conv1 = RGCNConv(input_dim, hidden_dim, num_relations=num_relations)
        self.conv2 = RGCNConv(hidden_dim, hidden_dim, num_relations=num_relations)
```

