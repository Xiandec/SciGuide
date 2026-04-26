# Ключевые листинги программной реализации

В приложении приведены сокращенные фрагменты кода, которые отражают библиотечное retrieval-ядро, фоновую обработку документов в backend и обучаемый графовый слой.

```python {#app-lst-pipeline-manager caption="PipelineManager как единая точка входа библиотеки"}
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
        self._text_chunker = self._get_or_create_text_chunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self._embedding_service = self._get_or_create_embedding_service(
            model_name=embedding_model_name,
            cache_dir=Path(model_cache_dir),
            token=huggingface_token,
        )
        self._vector_repository = QdrantVectorRepository(...)
        self._graph_repository = Neo4jGraphRepository(...)
        self._score_combiner = WeightedScoreCombiner(
            vector_weight=vector_weight,
            graph_weight=graph_weight,
            rerank_weight=rerank_weight,
        )

        self.chunking = ChunkingPipeline(self._chunking_use_case)
        self.search = SearchPipeline(
            self._search_use_case,
            default_limit=search_limit,
            default_candidate_limit=search_candidate_limit,
        )
```

```python {#app-lst-run-chunking caption="Индексация документа в библиотеке sciguide_pipeline"}
class RunChunking:
    """Orchestrates chunking, embedding, and persistence."""

    def execute(self, request: RunChunkingRequest) -> ChunkingReport:
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

        return ChunkingReport(
            documents_processed=len(request.documents),
            chunks_created=len(enriched_chunks),
            collection_name=self._collection_name,
            graph_namespace=self._graph_namespace,
        )
```

```python {#app-lst-run-search caption="Гибридный поиск: vector search и graph scoring"}
class RunSearch:
    """Execute vector search, graph scoring, and reranking."""

    def execute(self, request: RunSearchRequest) -> SearchReport:
        query_vector = self._embedding_service.embed_query(request.query)
        vector_candidates = self._vector_repository.search(
            query_vector=query_vector,
            limit=request.candidate_limit,
        )

        query_entities = self._entity_extractor.extract(request.query)
        query_tokens = self._entity_extractor.extract_tokens(request.query)
        chunk_ids = [candidate.chunk_id for candidate in vector_candidates]
        graph_scores = self._graph_repository.score_chunks(
            query_entities=query_entities,
            query_tokens=query_tokens,
            chunk_ids=chunk_ids,
        )

        vector_scores = {
            candidate.chunk_id: candidate.score
            for candidate in vector_candidates
        }
        combined_scores = self._score_combiner.combine(
            vector_scores=vector_scores,
            graph_scores=graph_scores,
            rerank_scores=None,
        )

        items = [
            SearchItem(
                chunk_id=candidate.chunk_id,
                document_id=str(candidate.payload.get("document_id", "")),
                text=str(candidate.payload.get("text", "")),
                metadata=dict(candidate.payload.get("metadata", {})),
                vector_score=vector_scores.get(candidate.chunk_id, 0.0),
                graph_score=graph_scores.get(candidate.chunk_id, 0.0),
                final_score=combined_scores.get(candidate.chunk_id, 0.0),
            )
            for candidate in vector_candidates
        ]
        return SearchReport(
            query=request.query,
            items=tuple(sorted(items, key=lambda item: item.final_score, reverse=True)),
            candidate_count=len(items),
        )
```

```python {#app-lst-process-document caption="Use case обработки документа в backend"}
class ProcessWorkspaceDocument:
    """Read a stored document and index it into retrieval stores."""

    async def execute(self, request: ProcessWorkspaceDocumentRequest) -> None:
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
                stage=DocumentStage.TEXT_EXTRACTION,
                error=None,
            )
            content_bytes = await self._document_storage.read_bytes(
                storage_key=document.storage_key,
            )

            current_stage = DocumentStage.CHUNKING
            document = await self._update_state(
                document=document,
                status=DocumentStatus.PROCESSING,
                stage=DocumentStage.CHUNKING,
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
```

```python {#app-lst-document-task caption="Celery-задача фоновой индексации документа"}
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
    pool = await asyncpg.create_pool(
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        host=settings.db_host,
        port=settings.db_port,
    )
    use_case = ProcessWorkspaceDocument(
        document_repository=PostgresWorkspaceDocumentRepository(pool),
        document_storage=MinioDocumentStorage(...),
        document_indexer=PipelineManagerWorkspaceDocumentIndexer(),
    )
    await use_case.execute(
        ProcessWorkspaceDocumentRequest(
            workspace_id=workspace_id,
            document_id=document_id,
        )
    )
```

```python {#app-lst-workspace-indexer caption="Связь документа воркспейса с PipelineManager"}
class PipelineManagerWorkspaceDocumentIndexer(WorkspaceDocumentIndexer):
    """Index documents with the shared SciGuide pipeline library."""

    async def index(
        self,
        *,
        document: WorkspaceDocument,
        content_bytes: bytes,
    ) -> None:
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
            qdrant_collection_name=collection_name,
            graph_namespace=collection_name,
            chunk_size=settings.pipeline_chunk_size,
            chunk_overlap=settings.pipeline_chunk_overlap,
            ...
        ) as manager:
            manager.chunking.run([source_document])
```

```python {#app-lst-assistant-retrieval caption="Retrieval контекста при генерации ответа"}
class OpenRouterAssistantResponder(AssistantResponder):
    """Generate assistant answers using retrieval and OpenRouter."""

    async def generate(
        self,
        request: AssistantResponderRequest,
    ) -> AssistantResponse:
        documents_used, snippets = await asyncio.to_thread(
            self._retrieve_context,
            request.workspace_id,
            request.user_message_content,
        )
        content = await self._generate_with_llm(
            request=request,
            snippets=snippets,
        )
        return AssistantResponse(
            content=content,
            documents_used=tuple(documents_used),
        )

    def _retrieve_context(
        self,
        workspace_id: UUID,
        query: str,
    ) -> tuple[list[MessageContextDocument], list[str]]:
        collection_name = (
            f"{settings.qdrant_collection_prefix}{workspace_id.hex}"
        )
        with PipelineManager(
            qdrant_collection_name=collection_name,
            graph_namespace=collection_name,
            search_limit=self._search_limit,
            search_candidate_limit=self._candidate_limit,
            ...
        ) as manager:
            report = manager.search.run(
                query=query,
                limit=self._search_limit,
                candidate_limit=self._candidate_limit,
            )

        documents_by_id: OrderedDict[str, MessageContextDocument] = OrderedDict()
        snippets = [
            f"[{index}] {item.metadata.get('filename', 'document')}: {item.text[:1200]}"
            for index, item in enumerate(report.items, start=1)
            if item.text.strip()
        ]
        return list(documents_by_id.values()), snippets
```

```python {#app-lst-gnn-features caption="Формирование признаков пары для обучаемого reranking-слоя"}
def candidate_features(query_id: str, doc_id: str) -> list[float]:
    rank = baseline_rank_lookup[query_id].get(
        doc_id,
        CANDIDATES_PER_QUERY + 1,
    )
    return [
        float(semantic_document_scores_by_query[query_id].get(doc_id, 0.0)),
        float(graph_document_scores_by_query[query_id].get(doc_id, 0.0)),
        float(baseline_document_scores_by_query[query_id].get(doc_id, 0.0)),
        1.0 / rank,
        1.0 - min(rank - 1, CANDIDATES_PER_QUERY) / CANDIDATES_PER_QUERY,
    ]


def model_rankings(
    model: nn.Module,
    query_ids: list[str],
    residual_alpha: float,
) -> dict[str, list[str]]:
    model.eval()
    rankings = {}
    with torch.no_grad():
        z = model.encode(data)
        for query_id in query_ids:
            doc_ids = candidates_by_query[query_id]
            pairs = torch.tensor(
                [
                    (
                        node_index[("query", query_id)],
                        node_index[("document", doc_id)],
                    )
                    for doc_id in doc_ids
                ],
                dtype=torch.long,
                device=device,
            ).t().contiguous()
            pair_features = candidate_feature_tensor(query_id, doc_ids)
            correction = normalize(
                model.decoder(z, pairs, pair_features).cpu().numpy()
            )
            scores = (
                candidate_baseline_scores(query_id, doc_ids)
                + residual_alpha * correction
            )
            rankings[query_id] = [
                doc_id
                for _, doc_id in sorted(zip(scores, doc_ids), reverse=True)
            ]
    return rankings
```

```python {#app-lst-gnn-models caption="Общий decoder и архитектура R-GCN"}
class LinkDecoder(nn.Module):
    def __init__(self, hidden_dim: int, dropout: float, feature_dim: int):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(hidden_dim * 4 + feature_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(
        self,
        z: torch.Tensor,
        pair_index: torch.Tensor,
        pair_features: torch.Tensor,
    ) -> torch.Tensor:
        q = z[pair_index[0]]
        d = z[pair_index[1]]
        graph_features = torch.cat(
            [q, d, torch.abs(q - d), q * d],
            dim=-1,
        )
        return self.mlp(
            torch.cat([graph_features, pair_features], dim=-1)
        ).squeeze(-1)


class RGCNModel(BaseReranker):
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        dropout: float,
        num_relations: int,
    ):
        super().__init__(hidden_dim, dropout)
        self.conv1 = RGCNConv(input_dim, hidden_dim, num_relations=num_relations)
        self.conv2 = RGCNConv(hidden_dim, hidden_dim, num_relations=num_relations)
```
