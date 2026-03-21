"""MinIO-backed storage for workspace documents."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO
from uuid import UUID

from workspace_documents.domain.repositories.document_storage import (
    DocumentStorage,
)

if TYPE_CHECKING:
    from minio import Minio


class MinioDocumentStorage(DocumentStorage):
    """Store workspace documents in a dedicated MinIO bucket."""

    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool,
        region: str | None = None,
        client: "Minio" | None = None,
    ) -> None:
        self._bucket_name = bucket_name
        self._region = region
        self._bucket_initialized = False
        self._client = client or self._build_client(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region,
        )

    async def save(
        self,
        *,
        workspace_id: UUID,
        document_id: UUID,
        filename: str,
        source: BinaryIO,
        size_bytes: int,
        content_type: str,
    ) -> str:
        """Upload a document stream into MinIO."""
        storage_key = self._build_storage_key(
            workspace_id=workspace_id,
            document_id=document_id,
            filename=filename,
        )
        self._ensure_bucket()
        source.seek(0)
        try:
            self._client.put_object(
                self._bucket_name,
                storage_key,
                source,
                length=size_bytes,
                content_type=content_type,
            )
        except Exception as exc:
            raise OSError("Failed to upload object to MinIO") from exc
        finally:
            source.seek(0)

        return storage_key

    async def delete(self, *, storage_key: str) -> None:
        """Delete a document object from MinIO."""
        self._ensure_bucket()
        try:
            self._client.remove_object(self._bucket_name, storage_key)
        except Exception as exc:
            raise OSError("Failed to delete object from MinIO") from exc

    async def read_bytes(self, *, storage_key: str) -> bytes:
        """Download stored document bytes from MinIO."""
        self._ensure_bucket()
        response = None
        try:
            response = self._client.get_object(self._bucket_name, storage_key)
            return response.read()
        except Exception as exc:
            raise OSError("Failed to read object from MinIO") from exc
        finally:
            if response is not None:
                response.close()
                response.release_conn()

    def _ensure_bucket(self) -> None:
        """Create bucket lazily on first use."""
        if self._bucket_initialized:
            return

        try:
            bucket_exists = self._client.bucket_exists(self._bucket_name)
            if not bucket_exists:
                self._client.make_bucket(
                    self._bucket_name,
                    location=self._region,
                )
        except Exception as exc:
            raise OSError("Failed to initialize MinIO bucket") from exc

        self._bucket_initialized = True

    @staticmethod
    def _build_storage_key(
        *,
        workspace_id: UUID,
        document_id: UUID,
        filename: str,
    ) -> str:
        """Build a stable MinIO object key for a workspace document."""
        normalized_filename = Path(filename).name.strip() or "document.bin"
        return f"{workspace_id}/{document_id}/{normalized_filename}"

    @staticmethod
    def _build_client(
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool,
        region: str | None,
    ) -> Any:
        """Instantiate MinIO client lazily to avoid hard import at module load."""
        from minio import Minio

        return Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region,
        )
