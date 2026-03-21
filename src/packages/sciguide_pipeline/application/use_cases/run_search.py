"""Use case for hybrid retrieval and reranking."""

from __future__ import annotations

from ..dto import RunSearchRequest
from ...domain.entities import SearchItem, SearchReport
from ...domain.repositories import GraphRepository, VectorRepository
from ...domain.services import (
    EmbeddingService,
    EntityExtractor,
    WeightedScoreCombiner,
)


class RunSearch:
    """Execute vector search, graph scoring, and reranking."""

    def __init__(
        self,
        entity_extractor: EntityExtractor,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository,
        graph_repository: GraphRepository,
        score_combiner: WeightedScoreCombiner,
    ) -> None:
        self._entity_extractor = entity_extractor
        self._embedding_service = embedding_service
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

        query_entities = self._entity_extractor.extract(request.query)
        query_tokens = self._entity_extractor.extract_tokens(request.query)
        chunk_ids = [candidate.chunk_id for candidate in vector_candidates]
        graph_scores = self._graph_repository.score_chunks(
            query_entities=query_entities,
            query_tokens=query_tokens,
            chunk_ids=chunk_ids,
        )
        graph_only_candidates = self._graph_repository.find_graph_only_matches(
            query_entities=query_entities,
            query_tokens=query_tokens,
            exclude_chunk_ids=chunk_ids,
            limit=request.limit,
        )

        vector_scores = {
            candidate.chunk_id: candidate.score
            for candidate in vector_candidates
        }
        for candidate in graph_only_candidates:
            vector_scores.setdefault(candidate.chunk_id, 0.0)
            graph_scores[candidate.chunk_id] = candidate.score

        combined_scores = self._score_combiner.combine(
            vector_scores=vector_scores,
            graph_scores=graph_scores,
            rerank_scores=None,
        )

        all_candidates = {
            candidate.chunk_id: candidate
            for candidate in vector_candidates
        }
        for candidate in graph_only_candidates:
            all_candidates.setdefault(candidate.chunk_id, candidate)

        if not all_candidates:
            return SearchReport(
                query=request.query,
                items=(),
                candidate_count=0,
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
                final_score=combined_scores.get(candidate.chunk_id, 0.0),
                graph_only=candidate.chunk_id not in chunk_ids,
            )
            for candidate in all_candidates.values()
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
            candidate_count=len(all_candidates),
        )
