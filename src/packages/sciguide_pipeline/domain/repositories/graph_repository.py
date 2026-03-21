"""Graph repository contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ..entities import TextChunk, VectorSearchMatch


class GraphRepository(ABC):
    """Abstraction over the graph storage used for structural ranking."""

    @abstractmethod
    def ensure_schema(self) -> None:
        """Ensure graph schema and indexes exist."""

    @abstractmethod
    def upsert_chunks(self, chunks: Sequence[TextChunk]) -> None:
        """Persist chunk-to-entity projections."""

    @abstractmethod
    def score_chunks(
        self,
        query_entities: Sequence[str],
        query_tokens: Sequence[str],
        chunk_ids: Sequence[str],
    ) -> dict[str, float]:
        """Return graph-based scores for candidate chunks."""

    @abstractmethod
    def find_graph_only_matches(
        self,
        query_entities: Sequence[str],
        query_tokens: Sequence[str],
        exclude_chunk_ids: Sequence[str],
        limit: int,
    ) -> list[VectorSearchMatch]:
        """Return graph-only chunk candidates outside vector retrieval."""

    @abstractmethod
    def close(self) -> None:
        """Release graph resources."""
