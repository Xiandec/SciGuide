"""Backward-compatible alias for the legacy concept extractor name."""

from __future__ import annotations

from .entity_extractor import EntityExtractor


class ConceptExtractor(EntityExtractor):
    """Legacy alias kept for compatibility with earlier package versions."""
