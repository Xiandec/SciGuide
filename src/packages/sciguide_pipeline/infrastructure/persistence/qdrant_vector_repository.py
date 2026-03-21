"""Qdrant vector repository adapter."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from ...domain.entities import TextChunk, VectorSearchMatch
from ...domain.exceptions import PipelineInitializationError
from ...domain.exceptions import MissingDependencyError
from ...domain.repositories import VectorRepository


class QdrantVectorRepository(VectorRepository):
    """Qdrant-backed vector store repository."""

    def __init__(
        self,
        url: str,
        collection_name: str,
        api_key: str | None = None,
        prefer_grpc: bool = False,
        timeout: float = 60.0,
    ) -> None:
        try:
            from qdrant_client import QdrantClient
        except ImportError as error:
            raise MissingDependencyError(
                "qdrant-client is required for vector storage."
            ) from error

        self._collection_name = collection_name
        self._client = QdrantClient(
            url=url,
            api_key=api_key,
            prefer_grpc=prefer_grpc,
            timeout=timeout,
        )

    @property
    def collection_name(self) -> str:
        """Return the configured collection name."""
        return self._collection_name

    def ensure_collection(self, vector_size: int) -> None:
        """Create the collection if it does not exist yet."""
        from qdrant_client.models import Distance, VectorParams

        if self._client.collection_exists(self._collection_name):
            self._ensure_existing_collection_matches(vector_size)
            return

        self._client.create_collection(
            collection_name=self._collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

    def upsert_chunks(
        self,
        chunks: Sequence[TextChunk],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        """Upsert chunk payloads and embeddings."""
        from qdrant_client.models import PointStruct

        points = [
            PointStruct(
                id=self._make_point_id(chunk.id),
                vector=list(embedding),
                payload={
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "text": chunk.text,
                    "sequence_number": chunk.sequence_number,
                    "entities": list(chunk.entities),
                    "metadata": self._sanitize_mapping(chunk.metadata),
                },
            )
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ]
        if points:
            self._client.upsert(
                collection_name=self._collection_name,
                points=points,
            )

    def search(
        self,
        query_vector: Sequence[float],
        limit: int,
    ) -> list[VectorSearchMatch]:
        """Search the collection for nearest chunks."""
        query_result = self._client.query_points(
            collection_name=self._collection_name,
            query=list(query_vector),
            limit=limit,
            with_payload=True,
        )
        results = list(getattr(query_result, "points", []) or [])

        return [
            VectorSearchMatch(
                chunk_id=str(
                    result.payload.get("chunk_id", "")
                    or getattr(result, "id", None)
                ),
                score=float(result.score),
                payload=dict(result.payload or {}),
            )
            for result in results
        ]

    def close(self) -> None:
        """Close the underlying client if supported."""
        close_method = getattr(self._client, "close", None)
        if callable(close_method):
            close_method()

    @classmethod
    def _sanitize_mapping(cls, mapping: dict[str, Any]) -> dict[str, Any]:
        return {
            key: cls._sanitize_value(value)
            for key, value in mapping.items()
        }

    @classmethod
    def _sanitize_value(cls, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            return cls._sanitize_mapping(value)
        if isinstance(value, (list, tuple, set)):
            return [cls._sanitize_value(item) for item in value]
        return str(value)

    @staticmethod
    def _make_point_id(chunk_id: str) -> str:
        return str(uuid5(NAMESPACE_URL, f"sciguide:{chunk_id}"))

    def _ensure_existing_collection_matches(
        self,
        vector_size: int,
    ) -> None:
        collection_info = self._client.get_collection(self._collection_name)
        actual_size = self._extract_vector_size(collection_info)
        if actual_size is None or actual_size == vector_size:
            return

        points_count = self._extract_points_count(collection_info)
        if points_count == 0:
            self._client.delete_collection(self._collection_name)
            self.ensure_collection(vector_size)
            return

        raise PipelineInitializationError(
            "Qdrant collection vector size mismatch: "
            f"collection '{self._collection_name}' uses size "
            f"{actual_size}, but the embedding model produces {vector_size}. "
            "Recreate the collection or align the configured embedding model."
        )

    @staticmethod
    def _extract_vector_size(collection_info: Any) -> int | None:
        config = getattr(collection_info, "config", None)
        params = getattr(config, "params", None)
        vectors = getattr(params, "vectors", None)

        size = getattr(vectors, "size", None)
        if isinstance(size, int):
            return size

        if isinstance(vectors, dict):
            first_vector = next(iter(vectors.values()), None)
            named_size = getattr(first_vector, "size", None)
            if isinstance(named_size, int):
                return named_size

        return None

    @staticmethod
    def _extract_points_count(collection_info: Any) -> int:
        for attribute_name in ("points_count", "vectors_count"):
            value = getattr(collection_info, attribute_name, None)
            if isinstance(value, int):
                return value
        return 0
