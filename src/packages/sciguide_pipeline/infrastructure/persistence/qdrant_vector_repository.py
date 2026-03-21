"""Qdrant vector repository adapter."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from ...domain.entities import TextChunk, VectorSearchMatch
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
        results = self._client.search(
            collection_name=self._collection_name,
            query_vector=list(query_vector),
            limit=limit,
            with_payload=True,
        )
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
