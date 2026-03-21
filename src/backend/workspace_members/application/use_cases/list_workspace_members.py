"""Use case for listing workspace members."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from workspace_members.application.dto.member_dto import (
    WorkspaceMemberDTO,
)
from workspace_members.application.dto.member_dto import (
    WorkspaceMemberListDTO,
)
from workspace_members.application.use_cases._workspace_access import (
    get_workspace_for_member_management,
)
from workspace_members.domain.repositories.workspace_member_repository import (
    WorkspaceMemberRepository,
)
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)


@dataclass(slots=True)
class ListWorkspaceMembersRequest:
    """Workspace members list request payload."""

    workspace_id: UUID
    actor_user_id: UUID


class ListWorkspaceMembers:
    """List members of a shared workspace for admins."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        workspace_member_repository: WorkspaceMemberRepository,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._workspace_member_repository = workspace_member_repository

    async def execute(
        self,
        request: ListWorkspaceMembersRequest,
    ) -> WorkspaceMemberListDTO:
        """Return workspace members for an admin actor."""
        await get_workspace_for_member_management(
            workspace_repository=self._workspace_repository,
            workspace_id=request.workspace_id,
            actor_user_id=request.actor_user_id,
        )
        members = await self._workspace_member_repository.list_by_workspace(
            workspace_id=request.workspace_id,
        )
        return WorkspaceMemberListDTO(
            items=[
                WorkspaceMemberDTO.from_entity(member)
                for member in members
            ],
        )
