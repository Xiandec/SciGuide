"""Workspace member routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Response
from fastapi import status

from shared.presentation.api.dependencies.security import (
    AuthenticatedPrincipal,
)
from shared.presentation.api.dependencies.security import get_current_principal
from workspace_members.application.use_cases.add_workspace_member import (
    AddWorkspaceMember,
)
from workspace_members.application.use_cases.add_workspace_member import (
    AddWorkspaceMemberRequest as AddWorkspaceMemberCommand,
)
from workspace_members.application.use_cases.list_workspace_members import (
    ListWorkspaceMembers,
)
from workspace_members.application.use_cases.list_workspace_members import (
    ListWorkspaceMembersRequest,
)
from workspace_members.application.use_cases.remove_workspace_member import (
    RemoveWorkspaceMember,
)
from workspace_members.application.use_cases.remove_workspace_member import (
    RemoveWorkspaceMemberRequest,
)
from workspace_members.application.use_cases.update_workspace_member import (
    UpdateWorkspaceMember,
)
from workspace_members.application.use_cases.update_workspace_member import (
    UpdateWorkspaceMemberRequest as UpdateWorkspaceMemberCommand,
)
from workspace_members.domain.exceptions.workspace_member_exceptions import (
    WorkspaceMemberAlreadyExistsError,
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
from workspace_members.domain.exceptions.workspace_member_exceptions import (
    WorkspaceMemberUserNotFoundError,
)
from workspace_members.presentation.api.dependencies import (
    get_add_workspace_member_use_case,
)
from workspace_members.presentation.api.dependencies import (
    get_list_workspace_members_use_case,
)
from workspace_members.presentation.api.dependencies import (
    get_remove_workspace_member_use_case,
)
from workspace_members.presentation.api.dependencies import (
    get_update_workspace_member_use_case,
)
from workspace_members.presentation.api.schemas.member_schemas import (
    AddWorkspaceMemberRequest,
)
from workspace_members.presentation.api.schemas.member_schemas import (
    UpdateWorkspaceMemberRequest,
)
from workspace_members.presentation.api.schemas.member_schemas import (
    WorkspaceMemberListResponse,
)
from workspace_members.presentation.api.schemas.member_schemas import (
    WorkspaceMemberResponse,
)
from workspaces.domain.entities.workspace import WorkspaceRole
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceAccessDeniedError,
)
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceNotFoundError,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/members",
    tags=["Workspace Members"],
)


@router.get(
    "",
    response_model=WorkspaceMemberListResponse,
    status_code=status.HTTP_200_OK,
    summary="Список участников",
)
async def list_members(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        ListWorkspaceMembers,
        Depends(get_list_workspace_members_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
) -> WorkspaceMemberListResponse:
    """Return workspace members."""
    try:
        members = await use_case.execute(
            ListWorkspaceMembersRequest(
                workspace_id=workspace_id,
                actor_user_id=principal.user_id,
            ),
        )
    except WorkspaceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except WorkspaceAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    return WorkspaceMemberListResponse(
        items=[
            WorkspaceMemberResponse(
                user_id=item.user_id,
                email=item.email,
                display_name=item.display_name,
                role=item.role,
                joined_at=item.joined_at,
            )
            for item in members.items
        ],
    )


@router.post(
    "",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Добавление участника",
)
async def add_member(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        AddWorkspaceMember,
        Depends(get_add_workspace_member_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
    payload: AddWorkspaceMemberRequest,
) -> WorkspaceMemberResponse:
    """Add a member to the workspace."""
    try:
        member = await use_case.execute(
            AddWorkspaceMemberCommand(
                workspace_id=workspace_id,
                actor_user_id=principal.user_id,
                user_id=payload.user_id,
                role=WorkspaceRole(payload.role.value),
            ),
        )
    except (WorkspaceNotFoundError, WorkspaceMemberUserNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except WorkspaceAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except WorkspaceMemberAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return WorkspaceMemberResponse(
        user_id=member.user_id,
        email=member.email,
        display_name=member.display_name,
        role=member.role,
        joined_at=member.joined_at,
    )


@router.patch(
    "/{user_id}",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_200_OK,
    summary="Изменение роли участника",
)
async def update_member_role(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        UpdateWorkspaceMember,
        Depends(get_update_workspace_member_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
    user_id: Annotated[UUID, Path()],
    payload: UpdateWorkspaceMemberRequest,
) -> WorkspaceMemberResponse:
    """Update member role."""
    try:
        member = await use_case.execute(
            UpdateWorkspaceMemberCommand(
                workspace_id=workspace_id,
                actor_user_id=principal.user_id,
                user_id=user_id,
                role=WorkspaceRole(payload.role.value),
            ),
        )
    except (WorkspaceNotFoundError, WorkspaceMemberNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except (
        WorkspaceAccessDeniedError,
        WorkspaceMemberOwnerImmutableError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except WorkspaceMemberLastAdminError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return WorkspaceMemberResponse(
        user_id=member.user_id,
        email=member.email,
        display_name=member.display_name,
        role=member.role,
        joined_at=member.joined_at,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление участника",
)
async def delete_member(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        RemoveWorkspaceMember,
        Depends(get_remove_workspace_member_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
    user_id: Annotated[UUID, Path()],
) -> Response:
    """Remove a member from the workspace."""
    try:
        await use_case.execute(
            RemoveWorkspaceMemberRequest(
                workspace_id=workspace_id,
                actor_user_id=principal.user_id,
                user_id=user_id,
            ),
        )
    except (WorkspaceNotFoundError, WorkspaceMemberNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except (
        WorkspaceAccessDeniedError,
        WorkspaceMemberOwnerImmutableError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except WorkspaceMemberLastAdminError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
