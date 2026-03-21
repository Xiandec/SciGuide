"""Embedding service contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence


class EmbeddingService(ABC):
    """Abstraction over the embeddings model."""

    @property
    @abstractmethod
    def vector_size(self) -> int:
        """Return the embedding vector size."""

    @abstractmethod
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed multiple documents."""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Embed a query string."""
