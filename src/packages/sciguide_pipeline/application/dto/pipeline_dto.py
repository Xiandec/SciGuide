"""DTOs for application use cases."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ...domain.entities import SourceDocument


@dataclass(frozen=True)
class RunChunkingRequest:
    """Input DTO for chunking."""

    documents: Sequence[SourceDocument]


@dataclass(frozen=True)
class RunSearchRequest:
    """Input DTO for retrieval."""

    query: str
    limit: int
    candidate_limit: int
