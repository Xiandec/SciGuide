"""PostgreSQL implementation of workspace prompt repository."""

from __future__ import annotations

from uuid import UUID

from asyncpg import Pool, Record

from workspace_prompt.domain.entities.workspace_prompt import WorkspacePrompt
from workspace_prompt.domain.entities.workspace_prompt import (
    WorkspacePromptAccess,
)
from workspace_prompt.domain.repositories.workspace_prompt_repository import (
    WorkspacePromptRepository,
)


class PostgresWorkspacePromptRepository(WorkspacePromptRepository):
    """Persist workspace prompts in PostgreSQL."""

    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def get_accessible_by_workspace_id(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
    ) -> WorkspacePromptAccess | None:
        """Load a prompt if the user can access the workspace."""
        record = await self._pool.fetchrow(
            """
            SELECT
                wp.workspace_id,
                wp.content,
                wp.created_at,
                wp.updated_at,
                wp.updated_by,
                CASE
                    WHEN w.owner_user_id = $2 THEN TRUE
                    WHEN wm.role = 'admin' THEN TRUE
                    ELSE FALSE
                END AS can_manage
            FROM workspace_prompts AS wp
            INNER JOIN workspaces AS w
                ON w.id = wp.workspace_id
            LEFT JOIN workspace_members AS wm
                ON wm.workspace_id = w.id
                AND wm.user_id = $2
            WHERE wp.workspace_id = $1
                AND (
                    w.owner_user_id = $2
                    OR wm.user_id IS NOT NULL
                    OR (
                        w.type = 'shared'
                        AND w.access_mode = 'global'
                    )
                )
            """,
            workspace_id,
            user_id,
        )
        if record is None:
            return None

        return WorkspacePromptAccess(
            prompt=self._build_prompt(record),
            can_manage=record["can_manage"],
        )

    async def update_content(
        self,
        *,
        workspace_id: UUID,
        content: str,
        updated_by: UUID,
    ) -> WorkspacePrompt | None:
        """Update prompt content and return the updated entity."""
        record = await self._pool.fetchrow(
            """
            UPDATE workspace_prompts
            SET
                content = $2,
                updated_by = $3
            WHERE workspace_id = $1
            RETURNING
                workspace_id,
                content,
                created_at,
                updated_at,
                updated_by
            """,
            workspace_id,
            content,
            updated_by,
        )
        if record is None:
            return None

        return self._build_prompt(record)

    @staticmethod
    def _build_prompt(record: Record) -> WorkspacePrompt:
        """Map a PostgreSQL row to a workspace prompt entity."""
        return WorkspacePrompt(
            workspace_id=record["workspace_id"],
            content=record["content"],
            created_at=record["created_at"],
            updated_at=record["updated_at"],
            updated_by=record["updated_by"],
        )
