"""PostgreSQL implementation of message repository."""

from __future__ import annotations

import base64
import json
from datetime import datetime
from uuid import UUID

from asyncpg import Pool, Record

from messages.domain.entities.message import ChatAccess
from messages.domain.entities.message import Message
from messages.domain.entities.message import MessageContextDocument
from messages.domain.entities.message import MessageRole
from messages.domain.entities.message import MessageStatus
from messages.domain.repositories.message_repository import MessageRepository


class PostgresMessageRepository(MessageRepository):
    """Persist chat messages in PostgreSQL."""

    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def get_chat_access(
        self,
        *,
        workspace_id: UUID,
        chat_id: UUID,
        user_id: UUID,
    ) -> ChatAccess | None:
        """Load a personal chat if it belongs to the actor."""
        record = await self._pool.fetchrow(
            """
            SELECT
                workspace_id,
                id AS chat_id,
                owner_user_id
            FROM chats
            WHERE workspace_id = $1
                AND id = $2
                AND owner_user_id = $3
            """,
            workspace_id,
            chat_id,
            user_id,
        )
        if record is None:
            return None

        return ChatAccess(
            workspace_id=record["workspace_id"],
            chat_id=record["chat_id"],
            owner_user_id=record["owner_user_id"],
        )

    async def list_by_chat(
        self,
        *,
        chat_id: UUID,
        limit: int,
        cursor: str | None,
    ) -> tuple[list[Message], str | None, bool]:
        """List chat messages in reverse chronological order."""
        cursor_created_at, cursor_message_id = self._decode_cursor(cursor)
        params: list[object] = [chat_id]
        where_parts = ["chat_id = $1"]

        if cursor_created_at is not None and cursor_message_id is not None:
            params.extend([cursor_created_at, cursor_message_id])
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
                chat_id,
                role,
                content,
                status,
                error_message,
                created_at
            FROM messages
            WHERE {' AND '.join(where_parts)}
            ORDER BY created_at DESC, id DESC
            LIMIT ${len(params)}
            """,
            *params,
        )

        has_more = len(records) > limit
        page_records = records[:limit]
        items = [self._build_message(record) for record in page_records]
        next_cursor = None
        if has_more and page_records:
            last_record = page_records[-1]
            next_cursor = self._encode_cursor(
                created_at=last_record["created_at"],
                message_id=last_record["id"],
            )

        return items, next_cursor, has_more

    async def list_recent_by_chat(
        self,
        *,
        chat_id: UUID,
        limit: int,
    ) -> list[Message]:
        """Load the latest messages in chronological order."""
        records = await self._pool.fetch(
            """
            SELECT
                id,
                chat_id,
                role,
                content,
                status,
                error_message,
                created_at
            FROM (
                SELECT
                    id,
                    chat_id,
                    role,
                    content,
                    status,
                    error_message,
                    created_at
                FROM messages
                WHERE chat_id = $1
                ORDER BY created_at DESC, id DESC
                LIMIT $2
            ) AS recent_messages
            ORDER BY created_at ASC, id ASC
            """,
            chat_id,
            limit,
        )
        return [self._build_message(record) for record in records]

    async def create_turn(
        self,
        *,
        user_message: Message,
        assistant_message: Message,
        context_documents: list[MessageContextDocument],
    ) -> tuple[Message, Message]:
        """Persist a user-assistant exchange atomically."""
        async with self._pool.acquire() as connection:
            async with connection.transaction():
                user_record = await connection.fetchrow(
                    """
                    INSERT INTO messages (
                        id,
                        chat_id,
                        role,
                        content,
                        status,
                        error_message,
                        created_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING
                        id,
                        chat_id,
                        role,
                        content,
                        status,
                        error_message,
                        created_at
                    """,
                    user_message.id,
                    user_message.chat_id,
                    user_message.role.value,
                    user_message.content,
                    user_message.status.value,
                    user_message.error_message,
                    user_message.created_at,
                )
                assistant_record = await connection.fetchrow(
                    """
                    INSERT INTO messages (
                        id,
                        chat_id,
                        role,
                        content,
                        status,
                        error_message,
                        created_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING
                        id,
                        chat_id,
                        role,
                        content,
                        status,
                        error_message,
                        created_at
                    """,
                    assistant_message.id,
                    assistant_message.chat_id,
                    assistant_message.role.value,
                    assistant_message.content,
                    assistant_message.status.value,
                    assistant_message.error_message,
                    assistant_message.created_at,
                )

                if context_documents:
                    await connection.executemany(
                        """
                        INSERT INTO message_context_documents (
                            message_id,
                            document_id,
                            rank
                        )
                        VALUES ($1, $2, $3)
                        """,
                        [
                            (
                                assistant_message.id,
                                item.document_id,
                                item.rank,
                            )
                            for item in context_documents
                        ],
                    )

                await connection.execute(
                    """
                    UPDATE chats
                    SET
                        updated_at = $2,
                        last_message_at = $2
                    WHERE id = $1
                    """,
                    assistant_message.chat_id,
                    assistant_message.created_at,
                )

        if user_record is None or assistant_record is None:
            raise RuntimeError("Failed to persist chat messages")

        return (
            self._build_message(user_record),
            self._build_message(assistant_record),
        )

    @staticmethod
    def _build_message(record: Record) -> Message:
        """Map a PostgreSQL row to a message entity."""
        return Message(
            id=record["id"],
            chat_id=record["chat_id"],
            role=MessageRole(record["role"]),
            content=record["content"],
            status=MessageStatus(record["status"]),
            created_at=record["created_at"],
            error_message=record["error_message"],
        )

    @staticmethod
    def _encode_cursor(
        *,
        created_at: datetime,
        message_id: UUID,
    ) -> str:
        """Encode message pagination cursor."""
        payload = json.dumps(
            {
                "created_at": created_at.isoformat(),
                "message_id": str(message_id),
            }
        ).encode("utf-8")
        return base64.urlsafe_b64encode(payload).decode("utf-8")

    @staticmethod
    def _decode_cursor(
        cursor: str | None,
    ) -> tuple[datetime | None, UUID | None]:
        """Decode message pagination cursor."""
        if not cursor:
            return None, None

        try:
            payload = base64.urlsafe_b64decode(cursor.encode("utf-8"))
            parsed = json.loads(payload.decode("utf-8"))
            return (
                datetime.fromisoformat(parsed["created_at"]),
                UUID(parsed["message_id"]),
            )
        except (
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise ValueError("Invalid pagination cursor") from exc
