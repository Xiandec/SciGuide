"""Vector repository contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ..entities import TextChunk, VectorSearchMatch


class VectorRepository(ABC):
    """Abstraction over the vector store used for retrieval."""

    @abstractmethod
    def ensure_collection(self, vector_size: int) -> None:
        """Ensure the vector collection exists."""

    @abstractmethod
    def upsert_chunks(
        self,
        chunks: Sequence[TextChunk],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        """Persist chunks and their embeddings."""

    @abstractmethod
    def search(
        self,
        query_vector: Sequence[float],
        limit: int,
    ) -> list[VectorSearchMatch]:
        """Search for the nearest chunks."""

    @abstractmethod
    def close(self) -> None:
        """Release vector store resources."""
