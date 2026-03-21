"""Mock workspace routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response, status

from shared.presentation.api.dependencies.security import get_current_principal
from shared.presentation.api.mock_data import BASE_TIME
from shared.presentation.api.mock_data import MOCK_CREATED_WORKSPACE_ID
from shared.presentation.api.mock_data import build_workspace
from shared.presentation.api.schemas.common import CursorPage
from workspaces.presentation.api.schemas.workspace_schemas import (
    CreateWorkspaceRequest,
)
from workspaces.presentation.api.schemas.workspace_schemas import (
    UpdateWorkspaceRequest,
)
from workspaces.presentation.api.schemas.workspace_schemas import (
    WorkspaceListResponse,
)
from workspaces.presentation.api.schemas.workspace_schemas import (
    WorkspaceResponse,
)

router = APIRouter(
    prefix="/workspaces",
    tags=["Workspaces"],
    dependencies=[Depends(get_current_principal)],
)


@router.get(
    "",
    response_model=WorkspaceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Список доступных воркспейсов",
)
async def list_workspaces(
    workspace_type: Annotated[
        str | None,
        Query(alias="type"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: Annotated[str | None, Query()] = None,
    sort: Annotated[str, Query()] = "-created_at",
) -> WorkspaceListResponse:
    """Return a mocked workspace collection."""

    workspace_one = build_workspace()
    workspace_two = build_workspace(
        workspace_id=MOCK_CREATED_WORKSPACE_ID,
        name="Graph Retrieval",
        description="Workspace for graph-guided retrieval experiments",
        workspace_type="shared",
        access_mode="by_membership",
    )

    items = [
        WorkspaceResponse(
            id=workspace_one["id"],
            name=workspace_one["name"],
            description=workspace_one["description"],
            type=workspace_one["type"],
            access_mode=workspace_one["access_mode"],
            my_role=workspace_one["my_role"],
            created_at=workspace_one["created_at"],
            updated_at=workspace_one["updated_at"],
        ),
        WorkspaceResponse(
            id=workspace_two["id"],
            name=workspace_two["name"],
            description=workspace_two["description"],
            type=workspace_two["type"],
            access_mode=workspace_two["access_mode"],
            my_role=workspace_two["my_role"],
            created_at=workspace_two["created_at"],
            updated_at=workspace_two["updated_at"],
        ),
    ]

    if workspace_type is not None:
        items = [item for item in items if item.type.value == workspace_type]

    return WorkspaceListResponse(
        items=items[:limit],
        page=CursorPage(next_cursor=cursor, has_more=False),
    )


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание воркспейса",
)
async def create_workspace(
    payload: CreateWorkspaceRequest,
) -> WorkspaceResponse:
    """Return a mocked created workspace."""

    workspace_payload = build_workspace(
        workspace_id=MOCK_CREATED_WORKSPACE_ID,
        name=payload.name,
        description=payload.description,
        workspace_type=payload.type.value,
        access_mode=payload.access_mode.value,
        created_at=BASE_TIME,
        updated_at=BASE_TIME,
    )

    return WorkspaceResponse(
        id=workspace_payload["id"],
        name=workspace_payload["name"],
        description=workspace_payload["description"],
        type=workspace_payload["type"],
        access_mode=workspace_payload["access_mode"],
        my_role=workspace_payload["my_role"],
        created_at=workspace_payload["created_at"],
        updated_at=workspace_payload["updated_at"],
    )


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение воркспейса",
)
async def get_workspace(
    workspace_id: Annotated[UUID, Path()],
) -> WorkspaceResponse:
    """Return a mocked workspace by id."""

    workspace_payload = build_workspace(
        workspace_id=workspace_id,
        workspace_type="shared"
        if workspace_id == MOCK_CREATED_WORKSPACE_ID
        else "private",
        access_mode="by_membership"
        if workspace_id == MOCK_CREATED_WORKSPACE_ID
        else "owner_only",
    )

    return WorkspaceResponse(
        id=workspace_payload["id"],
        name=workspace_payload["name"],
        description=workspace_payload["description"],
        type=workspace_payload["type"],
        access_mode=workspace_payload["access_mode"],
        my_role=workspace_payload["my_role"],
        created_at=workspace_payload["created_at"],
        updated_at=workspace_payload["updated_at"],
    )


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновление воркспейса",
)
async def update_workspace(
    workspace_id: Annotated[UUID, Path()],
    payload: UpdateWorkspaceRequest,
) -> WorkspaceResponse:
    """Return a mocked updated workspace."""

    base_workspace = build_workspace(workspace_id=workspace_id)

    return WorkspaceResponse(
        id=base_workspace["id"],
        name=payload.name or base_workspace["name"],
        description=(
            payload.description
            if payload.description is not None
            else base_workspace["description"]
        ),
        type=base_workspace["type"],
        access_mode=base_workspace["access_mode"],
        my_role=base_workspace["my_role"],
        created_at=base_workspace["created_at"],
        updated_at=BASE_TIME,
    )


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление воркспейса",
)
async def delete_workspace(
    workspace_id: Annotated[UUID, Path()],
) -> Response:
    """Acknowledge workspace deletion without body."""

    return Response(status_code=status.HTTP_204_NO_CONTENT)
