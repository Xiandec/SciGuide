"""Reranker service contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence


class RerankerService(ABC):
    """Abstraction over the cross-encoder reranker."""

    @abstractmethod
    def rerank(self, query: str, documents: Sequence[str]) -> list[float]:
        """Return relevance scores for query-document pairs."""
