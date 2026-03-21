"""Workspace prompt routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status

from shared.presentation.api.dependencies.security import (
    AuthenticatedPrincipal,
)
from shared.presentation.api.dependencies.security import get_current_principal
from workspace_prompt.application.use_cases.get_workspace_prompt import (
    GetWorkspacePrompt,
)
from workspace_prompt.application.use_cases.get_workspace_prompt import (
    GetWorkspacePromptRequest,
)
from workspace_prompt.application.use_cases.update_workspace_prompt import (
    UpdateWorkspacePrompt,
)
from workspace_prompt.application.use_cases.update_workspace_prompt import (
    UpdateWorkspacePromptRequest as UpdateWorkspacePromptCommand,
)
from workspace_prompt.domain.exceptions.workspace_prompt_exceptions import (
    WorkspacePromptAccessDeniedError,
)
from workspace_prompt.domain.exceptions.workspace_prompt_exceptions import (
    WorkspacePromptNotFoundError,
)
from workspace_prompt.presentation.api.dependencies import (
    get_get_workspace_prompt_use_case,
)
from workspace_prompt.presentation.api.dependencies import (
    get_update_workspace_prompt_use_case,
)
from workspace_prompt.presentation.api.schemas.prompt_schemas import (
    UpdateWorkspacePromptRequest,
)
from workspace_prompt.presentation.api.schemas.prompt_schemas import (
    WorkspacePromptResponse,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/prompt",
    tags=["Workspace Prompt"],
)


@router.get(
    "",
    response_model=WorkspacePromptResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение промпта",
)
async def get_prompt(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        GetWorkspacePrompt,
        Depends(get_get_workspace_prompt_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
) -> WorkspacePromptResponse:
    """Return workspace prompt details."""
    try:
        prompt = await use_case.execute(
            GetWorkspacePromptRequest(
                workspace_id=workspace_id,
                user_id=principal.user_id,
            ),
        )
    except WorkspacePromptNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return WorkspacePromptResponse(
        workspace_id=prompt.workspace_id,
        content=prompt.content,
        updated_at=prompt.updated_at,
        updated_by=prompt.updated_by,
    )


@router.put(
    "",
    response_model=WorkspacePromptResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновление промпта",
)
async def update_prompt(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        UpdateWorkspacePrompt,
        Depends(get_update_workspace_prompt_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
    payload: UpdateWorkspacePromptRequest,
) -> WorkspacePromptResponse:
    """Update workspace prompt content."""
    try:
        prompt = await use_case.execute(
            UpdateWorkspacePromptCommand(
                workspace_id=workspace_id,
                actor_user_id=principal.user_id,
                content=payload.content,
            ),
        )
    except WorkspacePromptNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except WorkspacePromptAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return WorkspacePromptResponse(
        workspace_id=prompt.workspace_id,
        content=prompt.content,
        updated_at=prompt.updated_at,
        updated_by=prompt.updated_by,
    )
