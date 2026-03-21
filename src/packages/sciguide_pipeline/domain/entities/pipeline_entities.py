"""Domain entities for chunking and retrieval pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class SourceDocument:
    """Source document passed to the library by a developer."""

    content: str | bytes
    metadata: dict[str, Any] = field(default_factory=dict)
    document_id: str | None = None
    source_name: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.content, bytes):
            text_content = self.content.decode("utf-8", errors="replace")
            object.__setattr__(self, "content", text_content)

        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("Document content must be a non-empty string.")

        if self.document_id is None:
            object.__setattr__(self, "document_id", uuid4().hex)


@dataclass(frozen=True)
class TextChunk:
    """Chunked text enriched with document context."""

    id: str
    document_id: str
    text: str
    sequence_number: int
    metadata: dict[str, Any] = field(default_factory=dict)
    entities: tuple[str, ...] = ()


@dataclass(frozen=True)
class VectorSearchMatch:
    """Candidate returned by the vector store."""

    chunk_id: str
    score: float
    payload: dict[str, Any]


@dataclass(frozen=True)
class ChunkingReport:
    """Chunking pipeline result."""

    documents_processed: int
    chunks_created: int
    collection_name: str
    graph_namespace: str


@dataclass(frozen=True)
class SearchItem:
    """Final ranked chunk returned to the developer."""

    chunk_id: str
    document_id: str
    text: str
    metadata: dict[str, Any]
    vector_score: float
    graph_score: float
    final_score: float
    graph_only: bool = False


@dataclass(frozen=True)
class SearchReport:
    """Search pipeline result."""

    query: str
    items: tuple[SearchItem, ...]
    candidate_count: int
