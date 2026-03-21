"""Pure domain service for combining retrieval scores."""

from __future__ import annotations


class WeightedScoreCombiner:
    """Combine vector, graph, and reranker scores into one score."""

    def __init__(
        self,
        vector_weight: float = 0.75,
        graph_weight: float = 0.25,
        rerank_weight: float = 0.0,
    ) -> None:
        total_weight = vector_weight + graph_weight + rerank_weight
        if total_weight <= 0:
            raise ValueError("At least one score weight must be positive.")

        self._vector_weight = vector_weight / total_weight
        self._graph_weight = graph_weight / total_weight
        self._rerank_weight = rerank_weight / total_weight

    def combine(
        self,
        vector_scores: dict[str, float],
        graph_scores: dict[str, float],
        rerank_scores: dict[str, float] | None = None,
    ) -> dict[str, float]:
        """Normalize each signal and combine them with configured weights."""
        resolved_rerank_scores = rerank_scores or {}
        normalized_vector = self._normalize(vector_scores)
        normalized_graph = self._normalize(graph_scores)
        normalized_rerank = self._normalize(resolved_rerank_scores)

        combined: dict[str, float] = {}
        chunk_ids = (
            set(vector_scores)
            | set(graph_scores)
            | set(resolved_rerank_scores)
        )
        for chunk_id in chunk_ids:
            combined[chunk_id] = (
                normalized_vector.get(chunk_id, 0.0) * self._vector_weight
                + normalized_graph.get(chunk_id, 0.0) * self._graph_weight
                + normalized_rerank.get(chunk_id, 0.0) * self._rerank_weight
            )

        return combined

    @staticmethod
    def _normalize(scores: dict[str, float]) -> dict[str, float]:
        if not scores:
            return {}

        min_score = min(scores.values())
        max_score = max(scores.values())
        if max_score == min_score:
            if max_score == 0.0:
                return {key: 0.0 for key in scores}
            return {key: 1.0 for key in scores}

        scale = max_score - min_score
        return {
            key: (value - min_score) / scale
            for key, value in scores.items()
        }
