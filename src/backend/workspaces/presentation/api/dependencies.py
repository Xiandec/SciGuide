"""Dependency wiring for workspace use cases."""

from __future__ import annotations

from functools import lru_cache

from asyncpg import Pool
from fastapi import Depends

from auth.presentation.api.dependencies import get_db_pool
from config import settings
from workspaces.application.use_cases.create_workspace import CreateWorkspace
from workspaces.application.use_cases.delete_workspace import DeleteWorkspace
from workspaces.application.use_cases.get_workspace import GetWorkspace
from workspaces.application.use_cases.list_workspaces import ListWorkspaces
from workspaces.application.use_cases.update_workspace import UpdateWorkspace
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)
from workspaces.domain.services.workspace_lifecycle_manager import (
    WorkspaceLifecycleManager,
)
from workspaces.infrastructure.lifecycle import HttpWorkspaceLifecycleManager
from workspaces.infrastructure.lifecycle import NoOpWorkspaceLifecycleManager
from workspaces.infrastructure.persistence import PostgresWorkspaceRepository


def get_workspace_repository(
    pool: Pool = Depends(get_db_pool),
) -> WorkspaceRepository:
    """Build workspace repository."""
    return PostgresWorkspaceRepository(pool)


@lru_cache(maxsize=1)
def get_workspace_lifecycle_manager() -> WorkspaceLifecycleManager:
    """Build workspace lifecycle manager."""
    if settings.workspace_lifecycle_mode == "http":
        return HttpWorkspaceLifecycleManager(
            qdrant_url=settings.qdrant_url,
            qdrant_collection_prefix=settings.qdrant_collection_prefix,
            qdrant_vector_size=settings.qdrant_vector_size,
            qdrant_distance=settings.qdrant_distance,
            neo4j_url=settings.neo4j_url,
            neo4j_username=settings.neo4j_username,
            neo4j_password=settings.neo4j_password,
            neo4j_database=settings.neo4j_database,
            neo4j_root_label=settings.neo4j_workspace_root_label,
            timeout_seconds=settings.workspace_lifecycle_timeout_seconds,
        )

    return NoOpWorkspaceLifecycleManager()


def get_list_workspaces_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
) -> ListWorkspaces:
    """Build list workspaces use case."""
    return ListWorkspaces(workspace_repository=workspace_repository)


def get_create_workspace_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
    lifecycle_manager: WorkspaceLifecycleManager = Depends(
        get_workspace_lifecycle_manager,
    ),
) -> CreateWorkspace:
    """Build create workspace use case."""
    return CreateWorkspace(
        workspace_repository=workspace_repository,
        lifecycle_manager=lifecycle_manager,
    )


def get_get_workspace_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
) -> GetWorkspace:
    """Build get workspace use case."""
    return GetWorkspace(workspace_repository=workspace_repository)


def get_update_workspace_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
) -> UpdateWorkspace:
    """Build update workspace use case."""
    return UpdateWorkspace(workspace_repository=workspace_repository)


def get_delete_workspace_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
    lifecycle_manager: WorkspaceLifecycleManager = Depends(
        get_workspace_lifecycle_manager,
    ),
) -> DeleteWorkspace:
    """Build delete workspace use case."""
    return DeleteWorkspace(
        workspace_repository=workspace_repository,
        lifecycle_manager=lifecycle_manager,
    )
