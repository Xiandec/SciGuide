"""Graph repository contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ..entities import TextChunk


class GraphRepository(ABC):
    """Abstraction over the graph storage used for structural ranking."""

    @abstractmethod
    def ensure_schema(self) -> None:
        """Ensure graph schema and indexes exist."""

    @abstractmethod
    def upsert_chunks(self, chunks: Sequence[TextChunk]) -> None:
        """Persist chunk-to-concept projections."""

    @abstractmethod
    def score_chunks(
        self,
        query_concepts: Sequence[str],
        chunk_ids: Sequence[str],
    ) -> dict[str, float]:
        """Return graph-based scores for candidate chunks."""

    @abstractmethod
    def close(self) -> None:
        """Release graph resources."""
