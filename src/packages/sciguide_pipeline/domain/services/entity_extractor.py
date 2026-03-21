"""Entity extraction contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence


class EntityExtractor(ABC):
    """Abstraction for deterministic entity extraction from text."""

    @abstractmethod
    def extract(self, text: str) -> Sequence[str]:
        """Extract normalized entity phrases from text."""

    @abstractmethod
    def extract_tokens(self, text: str) -> Sequence[str]:
        """Extract normalized standalone tokens from text."""
