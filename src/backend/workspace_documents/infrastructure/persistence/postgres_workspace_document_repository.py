"""PostgreSQL implementation of workspace document repository."""

from __future__ import annotations

import base64
import json
from datetime import datetime
from uuid import UUID

from asyncpg import Pool, Record

from workspace_documents.domain.entities.workspace_document import (
    DocumentStage,
)
from workspace_documents.domain.entities.workspace_document import (
    DocumentStatus,
)
from workspace_documents.domain.entities.workspace_document import (
    WorkspaceDocument,
)
from workspace_documents.domain.repositories.workspace_document_repository import (  # noqa: E501
    WorkspaceDocumentRepository,
)


class PostgresWorkspaceDocumentRepository(WorkspaceDocumentRepository):
    """Persist workspace documents in PostgreSQL."""

    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def list_by_workspace(
        self,
        *,
        workspace_id: UUID,
        limit: int,
        cursor: str | None,
    ) -> tuple[list[WorkspaceDocument], str | None, bool]:
        """List workspace documents in reverse chronological order."""
        cursor_created_at, cursor_document_id = self._decode_cursor(cursor)
        params: list[object] = [workspace_id]
        where_parts = ["workspace_id = $1"]

        if cursor_created_at is not None and cursor_document_id is not None:
            params.extend([cursor_created_at, cursor_document_id])
            where_parts.append(
                "("
                "created_at < $2 "
                "OR (created_at = $2 AND id < $3)"
                ")",
            )

        params.append(limit + 1)
        records = await self._pool.fetch(
            f"""
            SELECT
                id,
                workspace_id,
                filename,
                storage_key,
                content_type,
                size_bytes,
                status,
                processing_stage,
                processing_error,
                uploaded_by,
                created_at,
                updated_at
            FROM workspace_documents
            WHERE {' AND '.join(where_parts)}
            ORDER BY created_at DESC, id DESC
            LIMIT ${len(params)}
            """,
            *params,
        )

        has_more = len(records) > limit
        page_records = records[:limit]
        items = [self._build_document(record) for record in page_records]
        next_cursor = None
        if has_more and page_records:
            last_record = page_records[-1]
            next_cursor = self._encode_cursor(
                created_at=last_record["created_at"],
                document_id=last_record["id"],
            )

        return items, next_cursor, has_more

    async def create(
        self,
        document: WorkspaceDocument,
    ) -> WorkspaceDocument:
        """Create a document metadata row."""
        record = await self._pool.fetchrow(
            """
            INSERT INTO workspace_documents (
                id,
                workspace_id,
                filename,
                storage_key,
                content_type,
                size_bytes,
                status,
                processing_stage,
                processing_error,
                uploaded_by,
                created_at,
                updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING
                id,
                workspace_id,
                filename,
                storage_key,
                content_type,
                size_bytes,
                status,
                processing_stage,
                processing_error,
                uploaded_by,
                created_at,
                updated_at
            """,
            document.id,
            document.workspace_id,
            document.filename,
            document.storage_key,
            document.content_type,
            document.size_bytes,
            document.status.value,
            document.processing_stage.value,
            document.processing_error,
            document.uploaded_by,
            document.created_at,
            document.updated_at,
        )
        if record is None:
            raise RuntimeError("Failed to create workspace document")

        return self._build_document(record)

    async def get_by_id(
        self,
        *,
        workspace_id: UUID,
        document_id: UUID,
    ) -> WorkspaceDocument | None:
        """Load a workspace document by id."""
        record = await self._pool.fetchrow(
            """
            SELECT
                id,
                workspace_id,
                filename,
                storage_key,
                content_type,
                size_bytes,
                status,
                processing_stage,
                processing_error,
                uploaded_by,
                created_at,
                updated_at
            FROM workspace_documents
            WHERE workspace_id = $1
                AND id = $2
            """,
            workspace_id,
            document_id,
        )
        if record is None:
            return None

        return self._build_document(record)

    async def delete_by_id(
        self,
        *,
        workspace_id: UUID,
        document_id: UUID,
    ) -> WorkspaceDocument | None:
        """Delete a workspace document and return its metadata."""
        record = await self._pool.fetchrow(
            """
            DELETE FROM workspace_documents
            WHERE workspace_id = $1
                AND id = $2
            RETURNING
                id,
                workspace_id,
                filename,
                storage_key,
                content_type,
                size_bytes,
                status,
                processing_stage,
                processing_error,
                uploaded_by,
                created_at,
                updated_at
            """,
            workspace_id,
            document_id,
        )
        if record is None:
            return None

        return self._build_document(record)

    async def update_processing_state(
        self,
        *,
        workspace_id: UUID,
        document_id: UUID,
        status: str,
        processing_stage: str,
        processing_error: str | None,
    ) -> WorkspaceDocument | None:
        """Update processing state and return fresh document metadata."""
        record = await self._pool.fetchrow(
            """
            UPDATE workspace_documents
            SET
                status = $3,
                processing_stage = $4,
                processing_error = $5
            WHERE workspace_id = $1
                AND id = $2
            RETURNING
                id,
                workspace_id,
                filename,
                storage_key,
                content_type,
                size_bytes,
                status,
                processing_stage,
                processing_error,
                uploaded_by,
                created_at,
                updated_at
            """,
            workspace_id,
            document_id,
            status,
            processing_stage,
            processing_error,
        )
        if record is None:
            return None

        return self._build_document(record)

    @staticmethod
    def _build_document(record: Record) -> WorkspaceDocument:
        """Map a PostgreSQL row to a workspace document entity."""
        return WorkspaceDocument(
            id=record["id"],
            workspace_id=record["workspace_id"],
            filename=record["filename"],
            storage_key=record["storage_key"],
            content_type=record["content_type"],
            size_bytes=record["size_bytes"],
            status=DocumentStatus(record["status"]),
            processing_stage=DocumentStage(record["processing_stage"]),
            processing_error=record["processing_error"],
            uploaded_by=record["uploaded_by"],
            created_at=record["created_at"],
            updated_at=record["updated_at"],
        )

    @staticmethod
    def _encode_cursor(
        *,
        created_at: datetime,
        document_id: UUID,
    ) -> str:
        """Encode stable pagination cursor."""
        payload = json.dumps(
            {
                "created_at": created_at.isoformat(),
                "id": str(document_id),
            },
            separators=(",", ":"),
        ).encode("utf-8")
        return base64.urlsafe_b64encode(payload).decode("utf-8")

    @staticmethod
    def _decode_cursor(
        cursor: str | None,
    ) -> tuple[datetime | None, UUID | None]:
        """Decode pagination cursor."""
        if cursor is None:
            return None, None

        padded_cursor = cursor + "=" * (-len(cursor) % 4)
        payload = base64.urlsafe_b64decode(padded_cursor.encode("utf-8"))
        data = json.loads(payload.decode("utf-8"))
        return datetime.fromisoformat(data["created_at"]), UUID(data["id"])
