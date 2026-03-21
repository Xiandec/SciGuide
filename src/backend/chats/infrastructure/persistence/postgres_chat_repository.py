"""PostgreSQL implementation of chat repository."""

from __future__ import annotations

import base64
import json
from datetime import datetime
from uuid import UUID

from asyncpg import Pool, Record

from chats.domain.entities.chat import Chat
from chats.domain.repositories.chat_repository import ChatRepository


class PostgresChatRepository(ChatRepository):
    """Persist personal chats in PostgreSQL."""

    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def list_owned_by_workspace(
        self,
        *,
        workspace_id: UUID,
        owner_user_id: UUID,
        limit: int,
        cursor: str | None,
        sort_desc: bool,
    ) -> tuple[list[Chat], str | None, bool]:
        """List chats owned by a user in a workspace."""
        cursor_updated_at, cursor_chat_id = self._decode_cursor(cursor)
        order_direction = "DESC" if sort_desc else "ASC"
        cursor_operator = "<" if sort_desc else ">"

        where_parts = [
            "workspace_id = $1",
            "owner_user_id = $2",
        ]
        params: list[object] = [workspace_id, owner_user_id]

        if cursor_updated_at is not None and cursor_chat_id is not None:
            params.extend([cursor_updated_at, cursor_chat_id])
            updated_at_index = len(params) - 1
            chat_id_index = len(params)
            where_parts.append(
                "("
                f"updated_at {cursor_operator} ${updated_at_index} "
                f"OR (updated_at = ${updated_at_index} "
                f"AND id {cursor_operator} ${chat_id_index})"
                ")",
            )

        params.append(limit + 1)
        query = f"""
            SELECT
                id,
                workspace_id,
                owner_user_id,
                title,
                created_at,
                updated_at,
                last_message_at
            FROM chats
            WHERE {' AND '.join(where_parts)}
            ORDER BY updated_at {order_direction}, id {order_direction}
            LIMIT ${len(params)}
        """
        records = await self._pool.fetch(query, *params)

        has_more = len(records) > limit
        page_records = records[:limit]
        items = [self._build_chat(record) for record in page_records]

        next_cursor = None
        if has_more and page_records:
            last_record = page_records[-1]
            next_cursor = self._encode_cursor(
                updated_at=last_record["updated_at"],
                chat_id=last_record["id"],
            )

        return items, next_cursor, has_more

    async def create(self, chat: Chat) -> Chat:
        """Create a chat row."""
        record = await self._pool.fetchrow(
            """
            INSERT INTO chats (
                id,
                workspace_id,
                owner_user_id,
                title,
                created_at,
                updated_at,
                last_message_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING
                id,
                workspace_id,
                owner_user_id,
                title,
                created_at,
                updated_at,
                last_message_at
            """,
            chat.id,
            chat.workspace_id,
            chat.owner_user_id,
            chat.title,
            chat.created_at,
            chat.updated_at,
            chat.last_message_at,
        )
        if record is None:
            raise RuntimeError("Failed to create chat")

        return self._build_chat(record)

    async def get_owned_by_id(
        self,
        *,
        workspace_id: UUID,
        chat_id: UUID,
        owner_user_id: UUID,
    ) -> Chat | None:
        """Load a chat if it belongs to the current actor."""
        record = await self._pool.fetchrow(
            """
            SELECT
                id,
                workspace_id,
                owner_user_id,
                title,
                created_at,
                updated_at,
                last_message_at
            FROM chats
            WHERE workspace_id = $1
                AND id = $2
                AND owner_user_id = $3
            """,
            workspace_id,
            chat_id,
            owner_user_id,
        )
        if record is None:
            return None

        return self._build_chat(record)

    async def update_owned_title(
        self,
        *,
        workspace_id: UUID,
        chat_id: UUID,
        owner_user_id: UUID,
        title: str,
    ) -> Chat | None:
        """Update chat title for the owner."""
        record = await self._pool.fetchrow(
            """
            UPDATE chats
            SET title = $4
            WHERE workspace_id = $1
                AND id = $2
                AND owner_user_id = $3
            RETURNING
                id,
                workspace_id,
                owner_user_id,
                title,
                created_at,
                updated_at,
                last_message_at
            """,
            workspace_id,
            chat_id,
            owner_user_id,
            title,
        )
        if record is None:
            return None

        return self._build_chat(record)

    async def delete_owned(
        self,
        *,
        workspace_id: UUID,
        chat_id: UUID,
        owner_user_id: UUID,
    ) -> bool:
        """Delete a chat owned by the actor."""
        status = await self._pool.execute(
            """
            DELETE FROM chats
            WHERE workspace_id = $1
                AND id = $2
                AND owner_user_id = $3
            """,
            workspace_id,
            chat_id,
            owner_user_id,
        )
        return status.endswith("DELETE 1")

    @staticmethod
    def _build_chat(record: Record) -> Chat:
        """Map a PostgreSQL row to a chat entity."""
        return Chat(
            id=record["id"],
            workspace_id=record["workspace_id"],
            owner_user_id=record["owner_user_id"],
            title=record["title"],
            created_at=record["created_at"],
            updated_at=record["updated_at"],
            last_message_at=record["last_message_at"],
        )

    @staticmethod
    def _encode_cursor(*, updated_at: datetime, chat_id: UUID) -> str:
        """Encode stable cursor for pagination."""
        payload = json.dumps(
            {
                "updated_at": updated_at.isoformat(),
                "id": str(chat_id),
            },
            separators=(",", ":"),
        ).encode("utf-8")
        return base64.urlsafe_b64encode(payload).decode("utf-8")

    @staticmethod
    def _decode_cursor(
        cursor: str | None,
    ) -> tuple[datetime | None, UUID | None]:
        """Decode cursor payload."""
        if cursor is None:
            return None, None

        padded_cursor = cursor + "=" * (-len(cursor) % 4)
        payload = base64.urlsafe_b64decode(padded_cursor.encode("utf-8"))
        data = json.loads(payload.decode("utf-8"))
        return datetime.fromisoformat(data["updated_at"]), UUID(data["id"])
