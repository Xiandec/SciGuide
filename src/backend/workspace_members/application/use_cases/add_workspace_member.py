"""Use case for adding workspace members."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from workspace_members.application.dto.member_dto import (
    WorkspaceMemberDTO,
)
from workspace_members.application.use_cases._workspace_access import (
    get_workspace_for_member_management,
)
from workspace_members.domain.repositories.workspace_member_repository import (
    WorkspaceMemberRepository,
)
from workspaces.domain.entities.workspace import WorkspaceRole
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)


@dataclass(slots=True)
class AddWorkspaceMemberRequest:
    """Add workspace member request payload."""

    workspace_id: UUID
    actor_user_id: UUID
    user_id: UUID
    role: WorkspaceRole


class AddWorkspaceMember:
    """Add a member to a shared workspace."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        workspace_member_repository: WorkspaceMemberRepository,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._workspace_member_repository = workspace_member_repository

    async def execute(
        self,
        request: AddWorkspaceMemberRequest,
    ) -> WorkspaceMemberDTO:
        """Add a new workspace member."""
        await get_workspace_for_member_management(
            workspace_repository=self._workspace_repository,
            workspace_id=request.workspace_id,
            actor_user_id=request.actor_user_id,
        )
        member = await self._workspace_member_repository.add(
            workspace_id=request.workspace_id,
            user_id=request.user_id,
            role=request.role,
        )
        return WorkspaceMemberDTO.from_entity(member)
