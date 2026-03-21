"""Concept extraction contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence


class ConceptExtractor(ABC):
    """Abstraction for extracting concepts from text."""

    @abstractmethod
    def extract(self, text: str) -> Sequence[str]:
        """Extract normalized concepts from text."""
