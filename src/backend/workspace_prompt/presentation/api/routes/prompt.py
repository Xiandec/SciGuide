"""Mock workspace prompt routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status

from shared.presentation.api.dependencies.security import get_current_principal
from shared.presentation.api.mock_data import BASE_TIME
from shared.presentation.api.mock_data import MOCK_USER_ID
from shared.presentation.api.mock_data import build_prompt
from workspace_prompt.presentation.api.schemas.prompt_schemas import (
    UpdateWorkspacePromptRequest,
)
from workspace_prompt.presentation.api.schemas.prompt_schemas import (
    WorkspacePromptResponse,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/prompt",
    tags=["Workspace Prompt"],
    dependencies=[Depends(get_current_principal)],
)


@router.get(
    "",
    response_model=WorkspacePromptResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение промпта",
)
async def get_prompt(
    workspace_id: Annotated[UUID, Path()],
) -> WorkspacePromptResponse:
    """Return the mocked workspace prompt."""

    prompt_payload = build_prompt(workspace_id)
    return WorkspacePromptResponse(
        workspace_id=prompt_payload["workspace_id"],
        content=prompt_payload["content"],
        updated_at=prompt_payload["updated_at"],
        updated_by=prompt_payload["updated_by"],
    )


@router.put(
    "",
    response_model=WorkspacePromptResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновление промпта",
)
async def update_prompt(
    workspace_id: Annotated[UUID, Path()],
    payload: UpdateWorkspacePromptRequest,
) -> WorkspacePromptResponse:
    """Return a mocked updated workspace prompt."""

    return WorkspacePromptResponse(
        workspace_id=workspace_id,
        content=payload.content,
        updated_at=BASE_TIME,
        updated_by=MOCK_USER_ID,
    )
