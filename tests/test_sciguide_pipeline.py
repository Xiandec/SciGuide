"""Tests for the SciGuide pipeline library."""

from __future__ import annotations

from dataclasses import replace

from sciguide_pipeline.application.dto import (
    RunChunkingRequest,
    RunSearchRequest,
)
from sciguide_pipeline.application.use_cases import RunChunking, RunSearch
from sciguide_pipeline.domain.entities import (
    SourceDocument,
    TextChunk,
    VectorSearchMatch,
)
from sciguide_pipeline.domain.services import WeightedScoreCombiner
from sciguide_pipeline.presentation import pipeline_manager as manager_module


class FakeTextChunker:
    """Simple chunker for testing the use case."""

    def __init__(self, *args, **kwargs):
        _ = args, kwargs

    def chunk_documents(self, documents):
        document = documents[0]
        return [
            TextChunk(
                id=f"{document.document_id}:0",
                document_id=document.document_id or "",
                text="graph retrieval",
                sequence_number=0,
                metadata={"source_name": "paper-a"},
            ),
            TextChunk(
                id=f"{document.document_id}:1",
                document_id=document.document_id or "",
                text="semantic reranking",
                sequence_number=1,
                metadata={"source_name": "paper-a"},
            ),
        ]


class FakeConceptExtractor:
    """Simple concept extractor for testing."""

    def __init__(self, *args, **kwargs):
        _ = args, kwargs

    def extract(self, text):
        return [part.lower() for part in text.split()[:2]]


class FakeEmbeddingService:
    """Embedding service stub with eager initialization tracking."""

    initialized = 0

    def __init__(self, model_name=None, cache_dir=None, token=None):
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.token = token
        self.vector_size = 3
        type(self).initialized += 1

    def embed_documents(self, texts):
        return [[float(index), 0.0, 1.0] for index, _ in enumerate(texts)]

    def embed_query(self, text):
        return [1.0, 0.0, 1.0]


class FakeRerankerService:
    """Reranker stub with eager initialization tracking."""

    initialized = 0

    def __init__(self, model_name=None, cache_dir=None, token=None):
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.token = token
        type(self).initialized += 1

    def rerank(self, query, documents):
        scores = []
        for document in documents:
            if "reranking" in document:
                scores.append(0.95)
            else:
                scores.append(0.15)
        return scores


class FakeVectorRepository:
    """In-memory vector repository for testing."""

    last_instance = None

    def __init__(
        self,
        url=None,
        collection_name="chunks",
        api_key=None,
        prefer_grpc=False,
        timeout=60.0,
    ):
        self.url = url
        self.collection_name = collection_name
        self.api_key = api_key
        self.prefer_grpc = prefer_grpc
        self.timeout = timeout
        self.ensure_called_with = None
        self.closed = False
        self._items = []
        type(self).last_instance = self

    def ensure_collection(self, vector_size):
        self.ensure_called_with = vector_size

    def upsert_chunks(self, chunks, embeddings):
        self._items = [
            (
                chunk,
                embedding,
                {
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                },
            )
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ]

    def search(self, query_vector, limit):
        _ = query_vector
        items = []
        for chunk, _, payload in self._items[:limit]:
            score = 0.9 if "graph" in chunk.text else 0.6
            items.append(
                VectorSearchMatch(
                    chunk_id=chunk.id,
                    score=score,
                    payload=payload,
                )
            )
        return items

    def close(self):
        self.closed = True


class FakeGraphRepository:
    """In-memory graph repository for testing."""

    last_instance = None

    def __init__(
        self,
        uri=None,
        username=None,
        password=None,
        database="neo4j",
        namespace="chunks",
    ):
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.namespace = namespace
        self.ensure_called = 0
        self.closed = False
        self._chunks = []
        type(self).last_instance = self

    def ensure_schema(self):
        self.ensure_called += 1

    def upsert_chunks(self, chunks):
        self._chunks = list(chunks)

    def score_chunks(self, query_concepts, chunk_ids):
        scores = {}
        for chunk in self._chunks:
            score = len(set(query_concepts) & set(chunk.concepts))
            scores[chunk.id] = float(score)
        return {chunk_id: scores.get(chunk_id, 0.0) for chunk_id in chunk_ids}

    def close(self):
        self.closed = True


class FakeChatModel:
    """LLM stub used by the manager wiring test."""

    def __init__(
        self,
        api_key=None,
        model_name=None,
        base_url=None,
        request_timeout=60.0,
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url
        self.request_timeout = request_timeout


def test_run_chunking_indexes_chunks_and_graph():
    """Chunking use case persists enriched chunks to both repositories."""
    vector_repository = FakeVectorRepository(collection_name="papers")
    graph_repository = FakeGraphRepository(namespace="papers-graph")
    use_case = RunChunking(
        text_chunker=FakeTextChunker(),
        concept_extractor=FakeConceptExtractor(),
        embedding_service=FakeEmbeddingService(),
        vector_repository=vector_repository,
        graph_repository=graph_repository,
        collection_name="papers",
        graph_namespace="papers-graph",
    )

    report = use_case.execute(
        RunChunkingRequest(
            documents=[SourceDocument(content="Graph retrieval systems")]
        )
    )

    assert report.documents_processed == 1
    assert report.chunks_created == 2
    assert vector_repository.ensure_called_with == 3
    assert graph_repository.ensure_called == 1
    stored_chunk = vector_repository._items[0][0]
    assert stored_chunk.concepts == ("graph", "retrieval")


def test_run_search_combines_vector_graph_and_rerank_scores():
    """Search use case ranks candidates with all three scoring signals."""
    vector_repository = FakeVectorRepository(collection_name="papers")
    graph_repository = FakeGraphRepository(namespace="papers-graph")
    graph_chunk = TextChunk(
        id="doc-1:0",
        document_id="doc-1",
        text="graph retrieval primer",
        sequence_number=0,
        metadata={"source_name": "paper-a"},
        concepts=("graph", "retrieval"),
    )
    rerank_chunk = replace(
        graph_chunk,
        id="doc-1:1",
        text="semantic reranking walkthrough",
        sequence_number=1,
        concepts=("semantic", "reranking"),
    )
    vector_repository.upsert_chunks(
        [graph_chunk, rerank_chunk],
        [[1.0, 0.0, 1.0], [0.5, 0.0, 1.0]],
    )
    graph_repository.upsert_chunks([graph_chunk, rerank_chunk])

    use_case = RunSearch(
        concept_extractor=FakeConceptExtractor(),
        embedding_service=FakeEmbeddingService(),
        reranker_service=FakeRerankerService(),
        vector_repository=vector_repository,
        graph_repository=graph_repository,
        score_combiner=WeightedScoreCombiner(),
    )

    report = use_case.execute(
        RunSearchRequest(
            query="semantic reranking",
            limit=2,
            candidate_limit=5,
        )
    )

    assert report.candidate_count == 2
    assert report.items[0].chunk_id == "doc-1:1"
    assert report.items[0].final_score > report.items[1].final_score


def test_pipeline_manager_wires_pipelines_and_warms_up(monkeypatch):
    """Pipeline manager eagerly initializes models and repositories."""
    monkeypatch.setattr(
        manager_module,
        "OpenRouterChatModel",
        FakeChatModel,
    )
    monkeypatch.setattr(
        manager_module,
        "LangChainConceptExtractor",
        FakeConceptExtractor,
    )
    monkeypatch.setattr(
        manager_module,
        "LangChainTextChunker",
        FakeTextChunker,
    )
    monkeypatch.setattr(
        manager_module,
        "HuggingFaceEmbeddingService",
        FakeEmbeddingService,
    )
    monkeypatch.setattr(
        manager_module,
        "HuggingFaceRerankerService",
        FakeRerankerService,
    )
    monkeypatch.setattr(
        manager_module,
        "QdrantVectorRepository",
        FakeVectorRepository,
    )
    monkeypatch.setattr(
        manager_module,
        "Neo4jGraphRepository",
        FakeGraphRepository,
    )

    manager = manager_module.PipelineManager(
        qdrant_url="http://localhost:6333",
        qdrant_collection_name="papers",
        neo4j_uri="bolt://localhost:7687",
        neo4j_username="neo4j",
        neo4j_password="password",
        llm_api_key="openrouter-key",
        llm_model_name="openrouter/model",
        embedding_model_name="hf-embedding",
        reranker_model_name="hf-reranker",
        model_cache_dir="/tmp/sciguide-cache",
    )

    report = manager.chunking.run(
        [SourceDocument(content="Graph retrieval and semantic reranking")]
    )
    search_report = manager.search.run("semantic reranking", limit=2)

    assert report.chunks_created == 2
    assert search_report.items
    assert FakeEmbeddingService.initialized >= 1
    assert FakeRerankerService.initialized >= 1
    assert FakeVectorRepository.last_instance.ensure_called_with == 3
    assert FakeGraphRepository.last_instance.ensure_called >= 1

    manager.close()

    assert FakeVectorRepository.last_instance.closed is True
    assert FakeGraphRepository.last_instance.closed is True
