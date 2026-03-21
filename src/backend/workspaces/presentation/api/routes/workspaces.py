"""Workspace routes."""

from __future__ import annotations

from typing import Annotated
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from fastapi import status

from shared.presentation.api.dependencies.security import (
    AuthenticatedPrincipal,
)
from shared.presentation.api.dependencies.security import get_current_principal
from shared.presentation.api.schemas.common import CursorPage
from workspaces.application.use_cases.create_workspace import CreateWorkspace
from workspaces.application.use_cases.create_workspace import (
    CreateWorkspaceRequest as CreateWorkspaceCommand,
)
from workspaces.application.use_cases.delete_workspace import DeleteWorkspace
from workspaces.application.use_cases.delete_workspace import (
    DeleteWorkspaceRequest,
)
from workspaces.application.use_cases.get_workspace import GetWorkspace
from workspaces.application.use_cases.get_workspace import GetWorkspaceRequest
from workspaces.application.use_cases.list_workspaces import ListWorkspaces
from workspaces.application.use_cases.list_workspaces import (
    ListWorkspacesRequest,
)
from workspaces.application.use_cases.update_workspace import UpdateWorkspace
from workspaces.application.use_cases.update_workspace import (
    UpdateWorkspaceRequest as UpdateWorkspaceCommand,
)
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceAccessDeniedError,
)
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceLifecycleError,
)
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceNotFoundError,
)
from workspaces.presentation.api.dependencies import (
    get_create_workspace_use_case,
)
from workspaces.presentation.api.dependencies import (
    get_delete_workspace_use_case,
)
from workspaces.presentation.api.dependencies import (
    get_get_workspace_use_case,
)
from workspaces.presentation.api.dependencies import (
    get_list_workspaces_use_case,
)
from workspaces.presentation.api.dependencies import (
    get_update_workspace_use_case,
)
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
from workspaces.presentation.api.schemas.workspace_schemas import WorkspaceType

router = APIRouter(
    prefix="/workspaces",
    tags=["Workspaces"],
)


@router.get(
    "",
    response_model=WorkspaceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Список доступных воркспейсов",
)
async def list_workspaces(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        ListWorkspaces,
        Depends(get_list_workspaces_use_case),
    ],
    workspace_type: Annotated[
        WorkspaceType | None,
        Query(alias="type"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: Annotated[str | None, Query()] = None,
    sort: Annotated[
        Literal["-created_at", "created_at"],
        Query(),
    ] = "-created_at",
) -> WorkspaceListResponse:
    """Return accessible workspaces."""
    payload = await use_case.execute(
        ListWorkspacesRequest(
            user_id=principal.user_id,
            workspace_type=workspace_type,
            limit=limit,
            cursor=cursor,
            sort=sort,
        ),
    )

    return WorkspaceListResponse(
        items=[
            WorkspaceResponse(
                id=item.id,
                name=item.name,
                description=item.description,
                type=item.type,
                access_mode=item.access_mode,
                my_role=item.my_role,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in payload.items
        ],
        page=CursorPage(
            next_cursor=payload.next_cursor,
            has_more=payload.has_more,
        ),
    )


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание воркспейса",
)
async def create_workspace(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        CreateWorkspace,
        Depends(get_create_workspace_use_case),
    ],
    payload: CreateWorkspaceRequest,
) -> WorkspaceResponse:
    """Create a workspace."""
    try:
        workspace = await use_case.execute(
            CreateWorkspaceCommand(
                owner_user_id=principal.user_id,
                name=payload.name,
                description=payload.description,
                workspace_type=payload.type,
                access_mode=payload.access_mode,
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except WorkspaceLifecycleError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        type=workspace.type,
        access_mode=workspace.access_mode,
        my_role=workspace.my_role,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение воркспейса",
)
async def get_workspace(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        GetWorkspace,
        Depends(get_get_workspace_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
) -> WorkspaceResponse:
    """Return workspace details."""
    try:
        workspace = await use_case.execute(
            GetWorkspaceRequest(
                workspace_id=workspace_id,
                user_id=principal.user_id,
            ),
        )
    except WorkspaceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        type=workspace.type,
        access_mode=workspace.access_mode,
        my_role=workspace.my_role,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновление воркспейса",
)
async def update_workspace(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        UpdateWorkspace,
        Depends(get_update_workspace_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
    payload: UpdateWorkspaceRequest,
) -> WorkspaceResponse:
    """Update workspace metadata."""
    try:
        workspace = await use_case.execute(
            UpdateWorkspaceCommand(
                workspace_id=workspace_id,
                actor_user_id=principal.user_id,
                name=payload.name,
                description=payload.description,
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
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        type=workspace.type,
        access_mode=workspace.access_mode,
        my_role=workspace.my_role,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление воркспейса",
)
async def delete_workspace(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        DeleteWorkspace,
        Depends(get_delete_workspace_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
) -> Response:
    """Delete workspace metadata and external storage resources."""
    try:
        await use_case.execute(
            DeleteWorkspaceRequest(
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
    except WorkspaceLifecycleError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
