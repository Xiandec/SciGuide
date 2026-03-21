"""Use case for hybrid retrieval and reranking."""

from __future__ import annotations

from ..dto import RunSearchRequest
from ...domain.entities import SearchItem, SearchReport
from ...domain.repositories import GraphRepository, VectorRepository
from ...domain.services import (
    ConceptExtractor,
    EmbeddingService,
    RerankerService,
    WeightedScoreCombiner,
)


class RunSearch:
    """Execute vector search, graph scoring, and reranking."""

    def __init__(
        self,
        concept_extractor: ConceptExtractor,
        embedding_service: EmbeddingService,
        reranker_service: RerankerService,
        vector_repository: VectorRepository,
        graph_repository: GraphRepository,
        score_combiner: WeightedScoreCombiner,
    ) -> None:
        self._concept_extractor = concept_extractor
        self._embedding_service = embedding_service
        self._reranker_service = reranker_service
        self._vector_repository = vector_repository
        self._graph_repository = graph_repository
        self._score_combiner = score_combiner

    def execute(self, request: RunSearchRequest) -> SearchReport:
        """Execute the search workflow."""
        query_vector = self._embedding_service.embed_query(request.query)
        vector_candidates = self._vector_repository.search(
            query_vector=query_vector,
            limit=request.candidate_limit,
        )
        if not vector_candidates:
            return SearchReport(
                query=request.query,
                items=(),
                candidate_count=0,
            )

        query_concepts = self._concept_extractor.extract(request.query)
        chunk_ids = [candidate.chunk_id for candidate in vector_candidates]
        graph_scores = self._graph_repository.score_chunks(
            query_concepts=query_concepts,
            chunk_ids=chunk_ids,
        )

        texts = [
            str(candidate.payload.get("text", ""))
            for candidate in vector_candidates
        ]
        rerank_values = self._reranker_service.rerank(request.query, texts)

        vector_scores = {
            candidate.chunk_id: candidate.score
            for candidate in vector_candidates
        }
        rerank_scores = {
            candidate.chunk_id: score
            for candidate, score in zip(
                vector_candidates,
                rerank_values,
                strict=False,
            )
        }
        combined_scores = self._score_combiner.combine(
            vector_scores=vector_scores,
            graph_scores=graph_scores,
            rerank_scores=rerank_scores,
        )

        items = [
            SearchItem(
                chunk_id=candidate.chunk_id,
                document_id=str(
                    candidate.payload.get("document_id", "")
                ),
                text=str(candidate.payload.get("text", "")),
                metadata=dict(candidate.payload.get("metadata", {})),
                vector_score=vector_scores.get(candidate.chunk_id, 0.0),
                graph_score=graph_scores.get(candidate.chunk_id, 0.0),
                rerank_score=rerank_scores.get(candidate.chunk_id, 0.0),
                final_score=combined_scores.get(candidate.chunk_id, 0.0),
            )
            for candidate in vector_candidates
        ]
        ranked_items = tuple(
            sorted(
                items,
                key=lambda item: item.final_score,
                reverse=True,
            )[: request.limit]
        )

        return SearchReport(
            query=request.query,
            items=ranked_items,
            candidate_count=len(vector_candidates),
        )
