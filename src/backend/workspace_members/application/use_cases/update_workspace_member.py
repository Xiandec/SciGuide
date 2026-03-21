"""Use case for updating workspace member roles."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from workspace_members.application.dto.member_dto import (
    WorkspaceMemberDTO,
)
from workspace_members.application.use_cases._workspace_access import (
    get_workspace_for_member_management,
)
from workspace_members.domain.exceptions.workspace_member_exceptions import (
    WorkspaceMemberLastAdminError,
)
from workspace_members.domain.exceptions.workspace_member_exceptions import (
    WorkspaceMemberNotFoundError,
)
from workspace_members.domain.exceptions.workspace_member_exceptions import (
    WorkspaceMemberOwnerImmutableError,
)
from workspace_members.domain.repositories.workspace_member_repository import (
    WorkspaceMemberRepository,
)
from workspaces.domain.entities.workspace import WorkspaceRole
from workspaces.domain.repositories.workspace_repository import (
    WorkspaceRepository,
)


@dataclass(slots=True)
class UpdateWorkspaceMemberRequest:
    """Update workspace member role request payload."""

    workspace_id: UUID
    actor_user_id: UUID
    user_id: UUID
    role: WorkspaceRole


class UpdateWorkspaceMember:
    """Update the role of an existing workspace member."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        workspace_member_repository: WorkspaceMemberRepository,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._workspace_member_repository = workspace_member_repository

    async def execute(
        self,
        request: UpdateWorkspaceMemberRequest,
    ) -> WorkspaceMemberDTO:
        """Change the role of a workspace member."""
        workspace_access = await get_workspace_for_member_management(
            workspace_repository=self._workspace_repository,
            workspace_id=request.workspace_id,
            actor_user_id=request.actor_user_id,
        )

        if workspace_access.workspace.owner_user_id == request.user_id:
            raise WorkspaceMemberOwnerImmutableError()

        member = (
            await self._workspace_member_repository.get_by_workspace_and_user(
                workspace_id=request.workspace_id,
                user_id=request.user_id,
            )
        )
        if member is None:
            raise WorkspaceMemberNotFoundError(
                request.workspace_id,
                request.user_id,
            )

        if member.role == request.role:
            return WorkspaceMemberDTO.from_entity(member)

        if (
            member.role == WorkspaceRole.ADMIN
            and request.role != WorkspaceRole.ADMIN
        ):
            admin_count = await self._workspace_member_repository.count_admins(
                workspace_id=request.workspace_id,
            )
            if admin_count <= 1:
                raise WorkspaceMemberLastAdminError()

        updated_member = await self._workspace_member_repository.update_role(
            workspace_id=request.workspace_id,
            user_id=request.user_id,
            role=request.role,
        )
        if updated_member is None:
            raise WorkspaceMemberNotFoundError(
                request.workspace_id,
                request.user_id,
            )

        return WorkspaceMemberDTO.from_entity(updated_member)
