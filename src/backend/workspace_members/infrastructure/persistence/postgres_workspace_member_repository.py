"""PostgreSQL implementation of workspace member repository."""

from __future__ import annotations

from uuid import UUID

from asyncpg import ForeignKeyViolationError
from asyncpg import Pool, Record, UniqueViolationError

from workspace_members.domain.entities.workspace_member import (
    WorkspaceMember,
)
from workspace_members.domain.exceptions.workspace_member_exceptions import (
    WorkspaceMemberAlreadyExistsError,
)
from workspace_members.domain.exceptions.workspace_member_exceptions import (
    WorkspaceMemberUserNotFoundError,
)
from workspace_members.domain.repositories.workspace_member_repository import (
    WorkspaceMemberRepository,
)
from workspaces.domain.entities.workspace import WorkspaceRole
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceNotFoundError,
)


class PostgresWorkspaceMemberRepository(WorkspaceMemberRepository):
    """Persist workspace members in PostgreSQL."""

    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def list_by_workspace(
        self,
        *,
        workspace_id: UUID,
    ) -> list[WorkspaceMember]:
        """List workspace members enriched with user profile data."""
        records = await self._pool.fetch(
            """
            SELECT
                wm.workspace_id,
                wm.user_id,
                wm.role,
                wm.joined_at,
                u.email,
                u.display_name
            FROM workspace_members AS wm
            JOIN users AS u
                ON u.id = wm.user_id
            WHERE wm.workspace_id = $1
            ORDER BY
                CASE WHEN wm.role = 'admin' THEN 0 ELSE 1 END,
                wm.joined_at ASC,
                wm.user_id ASC
            """,
            workspace_id,
        )
        return [self._build_member(record) for record in records]

    async def get_by_workspace_and_user(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
    ) -> WorkspaceMember | None:
        """Load a single workspace member."""
        record = await self._pool.fetchrow(
            """
            SELECT
                wm.workspace_id,
                wm.user_id,
                wm.role,
                wm.joined_at,
                u.email,
                u.display_name
            FROM workspace_members AS wm
            JOIN users AS u
                ON u.id = wm.user_id
            WHERE wm.workspace_id = $1
                AND wm.user_id = $2
            """,
            workspace_id,
            user_id,
        )
        if record is None:
            return None

        return self._build_member(record)

    async def add(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
        role: WorkspaceRole,
    ) -> WorkspaceMember:
        """Add a workspace member."""
        try:
            record = await self._pool.fetchrow(
                """
                WITH inserted AS (
                    INSERT INTO workspace_members (
                        workspace_id,
                        user_id,
                        role
                    )
                    SELECT $1, u.id, $3
                    FROM users AS u
                    WHERE u.id = $2
                    RETURNING
                        workspace_id,
                        user_id,
                        role,
                        joined_at
                )
                SELECT
                    inserted.workspace_id,
                    inserted.user_id,
                    inserted.role,
                    inserted.joined_at,
                    u.email,
                    u.display_name
                FROM inserted
                JOIN users AS u
                    ON u.id = inserted.user_id
                """,
                workspace_id,
                user_id,
                role.value,
            )
        except UniqueViolationError as exc:
            raise WorkspaceMemberAlreadyExistsError(
                workspace_id,
                user_id,
            ) from exc
        except ForeignKeyViolationError as exc:
            raise WorkspaceNotFoundError(workspace_id) from exc

        if record is None:
            raise WorkspaceMemberUserNotFoundError(user_id)

        return self._build_member(record)

    async def update_role(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
        role: WorkspaceRole,
    ) -> WorkspaceMember | None:
        """Update a workspace member role."""
        record = await self._pool.fetchrow(
            """
            WITH updated AS (
                UPDATE workspace_members
                SET role = $3
                WHERE workspace_id = $1
                    AND user_id = $2
                RETURNING
                    workspace_id,
                    user_id,
                    role,
                    joined_at
            )
            SELECT
                updated.workspace_id,
                updated.user_id,
                updated.role,
                updated.joined_at,
                u.email,
                u.display_name
            FROM updated
            JOIN users AS u
                ON u.id = updated.user_id
            """,
            workspace_id,
            user_id,
            role.value,
        )
        if record is None:
            return None

        return self._build_member(record)

    async def remove(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Remove a workspace member row."""
        status = await self._pool.execute(
            """
            DELETE FROM workspace_members
            WHERE workspace_id = $1
                AND user_id = $2
            """,
            workspace_id,
            user_id,
        )
        return status.endswith("DELETE 1")

    async def count_admins(self, *, workspace_id: UUID) -> int:
        """Count workspace admins."""
        count = await self._pool.fetchval(
            """
            SELECT COUNT(*)
            FROM workspace_members
            WHERE workspace_id = $1
                AND role = 'admin'
            """,
            workspace_id,
        )
        return int(count or 0)

    @staticmethod
    def _build_member(record: Record) -> WorkspaceMember:
        """Build a domain member entity from a PostgreSQL row."""
        return WorkspaceMember(
            workspace_id=record["workspace_id"],
            user_id=record["user_id"],
            email=record["email"],
            display_name=record["display_name"],
            role=WorkspaceRole(record["role"]),
            joined_at=record["joined_at"],
        )
