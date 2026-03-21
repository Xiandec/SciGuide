"""Dependency wiring for workspace prompt use cases."""

from __future__ import annotations

from asyncpg import Pool
from fastapi import Depends

from auth.presentation.api.dependencies import get_db_pool
from workspace_prompt.application.use_cases.get_workspace_prompt import (
    GetWorkspacePrompt,
)
from workspace_prompt.application.use_cases.update_workspace_prompt import (
    UpdateWorkspacePrompt,
)
from workspace_prompt.domain.repositories.workspace_prompt_repository import (
    WorkspacePromptRepository,
)
from workspace_prompt.infrastructure.persistence import (
    PostgresWorkspacePromptRepository,
)


def get_workspace_prompt_repository(
    pool: Pool = Depends(get_db_pool),
) -> WorkspacePromptRepository:
    """Build workspace prompt repository."""
    return PostgresWorkspacePromptRepository(pool)


def get_get_workspace_prompt_use_case(
    workspace_prompt_repository: WorkspacePromptRepository = Depends(
        get_workspace_prompt_repository,
    ),
) -> GetWorkspacePrompt:
    """Build get workspace prompt use case."""
    return GetWorkspacePrompt(
        workspace_prompt_repository=workspace_prompt_repository,
    )


def get_update_workspace_prompt_use_case(
    workspace_prompt_repository: WorkspacePromptRepository = Depends(
        get_workspace_prompt_repository,
    ),
) -> UpdateWorkspacePrompt:
    """Build update workspace prompt use case."""
    return UpdateWorkspacePrompt(
        workspace_prompt_repository=workspace_prompt_repository,
    )
