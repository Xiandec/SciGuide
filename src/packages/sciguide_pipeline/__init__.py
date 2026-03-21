"""Public API for the SciGuide pipeline library."""

from .domain.entities import (
    ChunkingReport,
    SearchItem,
    SearchReport,
    SourceDocument,
)
from .presentation import PipelineManager

__all__ = [
    "ChunkingReport",
    "PipelineManager",
    "SearchItem",
    "SearchReport",
    "SourceDocument",
]
