"""Dependency wiring for workspace member use cases."""

from __future__ import annotations

from asyncpg import Pool
from fastapi import Depends

from auth.presentation.api.dependencies import get_db_pool
from workspace_members.application.use_cases.add_workspace_member import (
    AddWorkspaceMember,
)
from workspace_members.application.use_cases.list_workspace_members import (
    ListWorkspaceMembers,
)
from workspace_members.application.use_cases.remove_workspace_member import (
    RemoveWorkspaceMember,
)
from workspace_members.application.use_cases.update_workspace_member import (
    UpdateWorkspaceMember,
)
from workspace_members.domain.repositories.workspace_member_repository import (
    WorkspaceMemberRepository,
)
from workspace_members.infrastructure.persistence.postgres_workspace_member_repository import (  # noqa: E501
    PostgresWorkspaceMemberRepository,
)
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)
from workspaces.presentation.api.dependencies import (
    get_workspace_repository,
)


def get_workspace_member_repository(
    pool: Pool = Depends(get_db_pool),
) -> WorkspaceMemberRepository:
    """Build workspace member repository."""
    return PostgresWorkspaceMemberRepository(pool)


def get_list_workspace_members_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
    workspace_member_repository: WorkspaceMemberRepository = Depends(
        get_workspace_member_repository,
    ),
) -> ListWorkspaceMembers:
    """Build list workspace members use case."""
    return ListWorkspaceMembers(
        workspace_repository=workspace_repository,
        workspace_member_repository=workspace_member_repository,
    )


def get_add_workspace_member_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
    workspace_member_repository: WorkspaceMemberRepository = Depends(
        get_workspace_member_repository,
    ),
) -> AddWorkspaceMember:
    """Build add workspace member use case."""
    return AddWorkspaceMember(
        workspace_repository=workspace_repository,
        workspace_member_repository=workspace_member_repository,
    )


def get_update_workspace_member_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
    workspace_member_repository: WorkspaceMemberRepository = Depends(
        get_workspace_member_repository,
    ),
) -> UpdateWorkspaceMember:
    """Build update workspace member use case."""
    return UpdateWorkspaceMember(
        workspace_repository=workspace_repository,
        workspace_member_repository=workspace_member_repository,
    )


def get_remove_workspace_member_use_case(
    workspace_repository: WorkspaceRepository = Depends(
        get_workspace_repository,
    ),
    workspace_member_repository: WorkspaceMemberRepository = Depends(
        get_workspace_member_repository,
    ),
) -> RemoveWorkspaceMember:
    """Build remove workspace member use case."""
    return RemoveWorkspaceMember(
        workspace_repository=workspace_repository,
        workspace_member_repository=workspace_member_repository,
    )
