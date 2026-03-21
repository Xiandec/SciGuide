"""Hugging Face reranker adapter with eager model loading."""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ...domain.exceptions import MissingDependencyError
from ...domain.services import RerankerService


class HuggingFaceRerankerService(RerankerService):
    """Cross-encoder based reranker service."""

    def __init__(
        self,
        model_name: str,
        cache_dir: str | Path,
        token: str | None = None,
    ) -> None:
        self._cache_dir = Path(cache_dir)
        self._prepare_cache_dir()

        try:
            from sentence_transformers import CrossEncoder
        except ImportError as error:
            raise MissingDependencyError(
                "sentence-transformers is required for reranking."
            ) from error

        model_kwargs: dict[str, Any] = {
            "cache_folder": str(self._cache_dir),
        }
        if token is not None:
            model_kwargs["token"] = token

        self._model = CrossEncoder(model_name, **model_kwargs)

    def rerank(self, query: str, documents: Sequence[str]) -> list[float]:
        """Return reranker scores for candidate chunks."""
        if not documents:
            return []

        pairs = [[query, document] for document in documents]
        raw_scores = self._model.predict(pairs)
        return [float(score) for score in raw_scores.tolist()]

    def _prepare_cache_dir(self) -> None:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("HF_HOME", str(self._cache_dir))
        os.environ.setdefault("TRANSFORMERS_CACHE", str(self._cache_dir))
