"""Mock workspace member routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Response, status

from shared.presentation.api.dependencies.security import get_current_principal
from shared.presentation.api.mock_data import MOCK_MEMBER_USER_ID
from shared.presentation.api.mock_data import MOCK_USER_EMAIL
from shared.presentation.api.mock_data import MOCK_USER_ID
from shared.presentation.api.mock_data import build_member
from workspace_members.presentation.api.schemas.member_schemas import (
    AddWorkspaceMemberRequest,
)
from workspace_members.presentation.api.schemas.member_schemas import (
    MemberRole,
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

router = APIRouter(
    prefix="/workspaces/{workspace_id}/members",
    tags=["Workspace Members"],
    dependencies=[Depends(get_current_principal)],
)


@router.get(
    "",
    response_model=WorkspaceMemberListResponse,
    status_code=status.HTTP_200_OK,
    summary="Список участников",
)
async def list_members(
    workspace_id: Annotated[UUID, Path()],
) -> WorkspaceMemberListResponse:
    """Return mocked shared workspace members."""

    member_one = build_member()
    member_two = build_member(
        user_id=MOCK_MEMBER_USER_ID,
        email="researcher@example.com",
        display_name="Anna Smirnova",
        role=MemberRole.USER.value,
    )

    return WorkspaceMemberListResponse(
        items=[
            WorkspaceMemberResponse(
                user_id=member_one["user_id"],
                email=member_one["email"],
                display_name=member_one["display_name"],
                role=member_one["role"],
                joined_at=member_one["joined_at"],
            ),
            WorkspaceMemberResponse(
                user_id=member_two["user_id"],
                email=member_two["email"],
                display_name=member_two["display_name"],
                role=member_two["role"],
                joined_at=member_two["joined_at"],
            ),
        ],
    )


@router.post(
    "",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Добавление участника",
)
async def add_member(
    workspace_id: Annotated[UUID, Path()],
    payload: AddWorkspaceMemberRequest,
) -> WorkspaceMemberResponse:
    """Return a mocked added member."""

    email = (
        MOCK_USER_EMAIL
        if payload.user_id == MOCK_USER_ID
        else "researcher@example.com"
    )
    display_name = (
        "Ivan Petrov"
        if payload.user_id == MOCK_USER_ID
        else "Anna Smirnova"
    )

    member_payload = build_member(
        user_id=payload.user_id,
        email=email,
        display_name=display_name,
        role=payload.role.value,
    )

    return WorkspaceMemberResponse(
        user_id=member_payload["user_id"],
        email=member_payload["email"],
        display_name=member_payload["display_name"],
        role=member_payload["role"],
        joined_at=member_payload["joined_at"],
    )


@router.patch(
    "/{user_id}",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_200_OK,
    summary="Изменение роли участника",
)
async def update_member_role(
    workspace_id: Annotated[UUID, Path()],
    user_id: Annotated[UUID, Path()],
    payload: UpdateWorkspaceMemberRequest,
) -> WorkspaceMemberResponse:
    """Return a mocked updated member role."""

    member_payload = build_member(
        user_id=user_id,
        email="researcher@example.com",
        display_name="Anna Smirnova",
        role=payload.role.value,
    )

    return WorkspaceMemberResponse(
        user_id=member_payload["user_id"],
        email=member_payload["email"],
        display_name=member_payload["display_name"],
        role=member_payload["role"],
        joined_at=member_payload["joined_at"],
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление участника",
)
async def delete_member(
    workspace_id: Annotated[UUID, Path()],
    user_id: Annotated[UUID, Path()],
) -> Response:
    """Acknowledge member deletion without body."""

    return Response(status_code=status.HTTP_204_NO_CONTENT)
