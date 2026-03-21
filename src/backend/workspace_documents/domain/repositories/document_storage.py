"""Document storage contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import BinaryIO
from uuid import UUID


class DocumentStorage(ABC):
    """Abstract file storage for workspace documents."""

    @abstractmethod
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
        """Persist raw document content and return storage key."""

    @abstractmethod
    async def delete(self, *, storage_key: str) -> None:
        """Delete stored document content."""

    @abstractmethod
    async def read_bytes(self, *, storage_key: str) -> bytes:
        """Load stored document bytes by storage key."""
