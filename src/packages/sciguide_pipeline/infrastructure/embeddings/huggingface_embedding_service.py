"""Hugging Face embeddings adapter with eager model loading."""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ...domain.exceptions import MissingDependencyError
from ...domain.services import EmbeddingService


class HuggingFaceEmbeddingService(EmbeddingService):
    """Sentence-transformers based embedding service."""

    def __init__(
        self,
        model_name: str,
        cache_dir: str | Path,
        token: str | None = None,
    ) -> None:
        self._cache_dir = Path(cache_dir)
        self._prepare_cache_dir()

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise MissingDependencyError(
                "sentence-transformers is required for embeddings."
            ) from error

        model_kwargs: dict[str, Any] = {
            "cache_folder": str(self._cache_dir),
        }
        if token is not None:
            model_kwargs["token"] = token

        self._model = SentenceTransformer(model_name, **model_kwargs)
        self._vector_size = int(
            self._model.get_sentence_embedding_dimension()
        )

    @property
    def vector_size(self) -> int:
        """Return the dimension of produced embeddings."""
        return self._vector_size

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed multiple texts."""
        if not texts:
            return []

        embeddings = self._model.encode(
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return self._to_nested_list(embeddings)

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        embedding = self._model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return self._to_list(embedding)

    def _prepare_cache_dir(self) -> None:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("HF_HOME", str(self._cache_dir))
        os.environ.setdefault("TRANSFORMERS_CACHE", str(self._cache_dir))

    @staticmethod
    def _to_nested_list(embeddings: Any) -> list[list[float]]:
        return [
            [float(value) for value in row]
            for row in embeddings.tolist()
        ]

    @staticmethod
    def _to_list(embedding: Any) -> list[float]:
        return [float(value) for value in embedding.tolist()]
