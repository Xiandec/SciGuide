"""PostgreSQL implementation of workspace repository."""

from __future__ import annotations

import base64
import json
from datetime import datetime
from uuid import UUID

from asyncpg import Pool, Record

from workspaces.domain.entities.workspace import Workspace
from workspaces.domain.entities.workspace import WorkspaceAccess
from workspaces.domain.entities.workspace import WorkspaceAccessMode
from workspaces.domain.entities.workspace import WorkspaceRole
from workspaces.domain.entities.workspace import WorkspaceType
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)


class PostgresWorkspaceRepository(WorkspaceRepository):
    """Persist workspaces in PostgreSQL."""

    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def list_accessible(
        self,
        *,
        user_id: UUID,
        workspace_type: WorkspaceType | None,
        limit: int,
        cursor: str | None,
        sort_desc: bool,
    ) -> tuple[list[WorkspaceAccess], str | None, bool]:
        """List workspaces available to the user."""
        cursor_created_at, cursor_id = self._decode_cursor(cursor)
        order_direction = "DESC" if sort_desc else "ASC"
        cursor_operator = "<" if sort_desc else ">"

        where_parts = [self._accessible_clause()]
        params: list[object] = [user_id]

        if workspace_type is not None:
            params.append(workspace_type.value)
            where_parts.append(f"w.type = ${len(params)}")

        if cursor_created_at is not None and cursor_id is not None:
            params.extend([cursor_created_at, cursor_id])
            created_at_index = len(params) - 1
            id_index = len(params)
            where_parts.append(
                "("
                f"w.created_at {cursor_operator} ${created_at_index} "
                f"OR (w.created_at = ${created_at_index} "
                f"AND w.id {cursor_operator} ${id_index})"
                ")",
            )

        params.append(limit + 1)
        query = f"""
            SELECT
                w.id,
                w.owner_user_id,
                w.name,
                w.description,
                w.type,
                w.access_mode,
                w.created_at,
                w.updated_at,
                CASE
                    WHEN w.owner_user_id = $1 THEN 'admin'
                    WHEN wm.role IS NOT NULL THEN wm.role
                    WHEN w.access_mode = 'global' THEN 'user'
                    ELSE NULL
                END AS my_role
            FROM workspaces AS w
            LEFT JOIN workspace_members AS wm
                ON wm.workspace_id = w.id
                AND wm.user_id = $1
            WHERE {' AND '.join(where_parts)}
            ORDER BY w.created_at {order_direction}, w.id {order_direction}
            LIMIT ${len(params)}
        """
        records = await self._pool.fetch(query, *params)

        has_more = len(records) > limit
        page_records = records[:limit]
        items = [
            self._build_workspace_access(record)
            for record in page_records
        ]

        next_cursor = None
        if has_more and page_records:
            last_record = page_records[-1]
            next_cursor = self._encode_cursor(
                created_at=last_record["created_at"],
                workspace_id=last_record["id"],
            )

        return items, next_cursor, has_more

    async def create(self, workspace: Workspace) -> WorkspaceAccess:
        """Create a workspace row."""
        record = await self._pool.fetchrow(
            """
            INSERT INTO workspaces (
                id,
                owner_user_id,
                name,
                description,
                type,
                access_mode,
                created_at,
                updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING
                id,
                owner_user_id,
                name,
                description,
                type,
                access_mode,
                created_at,
                updated_at
            """,
            workspace.id,
            workspace.owner_user_id,
            workspace.name,
            workspace.description,
            workspace.type.value,
            workspace.access_mode.value,
            workspace.created_at,
            workspace.updated_at,
        )
        if record is None:
            raise RuntimeError("Failed to create workspace")

        return WorkspaceAccess(
            workspace=self._build_workspace(record),
            my_role=WorkspaceRole.ADMIN,
        )

    async def get_accessible_by_id(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
    ) -> WorkspaceAccess | None:
        """Load a workspace if the user can access it."""
        record = await self._pool.fetchrow(
            f"""
            SELECT
                w.id,
                w.owner_user_id,
                w.name,
                w.description,
                w.type,
                w.access_mode,
                w.created_at,
                w.updated_at,
                CASE
                    WHEN w.owner_user_id = $2 THEN 'admin'
                    WHEN wm.role IS NOT NULL THEN wm.role
                    WHEN w.access_mode = 'global' THEN 'user'
                    ELSE NULL
                END AS my_role
            FROM workspaces AS w
            LEFT JOIN workspace_members AS wm
                ON wm.workspace_id = w.id
                AND wm.user_id = $2
            WHERE w.id = $1
                AND {self._accessible_clause(user_id_param_index=2)}
            """,
            workspace_id,
            user_id,
        )
        if record is None:
            return None

        return self._build_workspace_access(record)

    async def update_owned(
        self,
        *,
        workspace_id: UUID,
        owner_user_id: UUID,
        name: str,
        description: str | None,
    ) -> WorkspaceAccess | None:
        """Update a workspace owned by the actor."""
        record = await self._pool.fetchrow(
            """
            UPDATE workspaces
            SET
                name = $3,
                description = $4
            WHERE id = $1
                AND owner_user_id = $2
            RETURNING
                id,
                owner_user_id,
                name,
                description,
                type,
                access_mode,
                created_at,
                updated_at
            """,
            workspace_id,
            owner_user_id,
            name,
            description,
        )
        if record is None:
            return None

        return WorkspaceAccess(
            workspace=self._build_workspace(record),
            my_role=WorkspaceRole.ADMIN,
        )

    async def delete_owned(
        self,
        *,
        workspace_id: UUID,
        owner_user_id: UUID,
    ) -> bool:
        """Delete a workspace owned by the actor."""
        status = await self._pool.execute(
            """
            DELETE FROM workspaces
            WHERE id = $1
                AND owner_user_id = $2
            """,
            workspace_id,
            owner_user_id,
        )
        return status.endswith("DELETE 1")

    async def delete_by_id(self, *, workspace_id: UUID) -> bool:
        """Delete a workspace by id."""
        status = await self._pool.execute(
            """
            DELETE FROM workspaces
            WHERE id = $1
            """,
            workspace_id,
        )
        return status.endswith("DELETE 1")

    @staticmethod
    def _accessible_clause(user_id_param_index: int = 1) -> str:
        """Build access predicate for listing and lookup."""
        return (
            f"w.owner_user_id = ${user_id_param_index} "
            "OR wm.user_id IS NOT NULL "
            "OR (w.type = 'shared' AND w.access_mode = 'global')"
        )

    @staticmethod
    def _build_workspace(record: Record) -> Workspace:
        """Map a PostgreSQL row to a workspace entity."""
        return Workspace(
            id=record["id"],
            owner_user_id=record["owner_user_id"],
            name=record["name"],
            description=record["description"],
            type=WorkspaceType(record["type"]),
            access_mode=WorkspaceAccessMode(record["access_mode"]),
            created_at=record["created_at"],
            updated_at=record["updated_at"],
        )

    def _build_workspace_access(self, record: Record) -> WorkspaceAccess:
        """Map a PostgreSQL row to an accessible workspace projection."""
        return WorkspaceAccess(
            workspace=self._build_workspace(record),
            my_role=WorkspaceRole(record["my_role"]),
        )

    @staticmethod
    def _encode_cursor(
        *,
        created_at: datetime,
        workspace_id: UUID,
    ) -> str:
        """Encode stable cursor for pagination."""
        payload = json.dumps(
            {
                "created_at": created_at.isoformat(),
                "id": str(workspace_id),
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
        return datetime.fromisoformat(data["created_at"]), UUID(data["id"])
