"""Text chunking contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ..entities import SourceDocument, TextChunk


class TextChunker(ABC):
    """Abstraction over text splitting logic."""

    @abstractmethod
    def chunk_documents(
        self,
        documents: Sequence[SourceDocument],
    ) -> list[TextChunk]:
        """Split source documents into indexed chunks."""
