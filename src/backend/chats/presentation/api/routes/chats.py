"""Mock chat routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response, status

from chats.presentation.api.schemas.chat_schemas import ChatListResponse
from chats.presentation.api.schemas.chat_schemas import ChatResponse
from chats.presentation.api.schemas.chat_schemas import CreateChatRequest
from chats.presentation.api.schemas.chat_schemas import UpdateChatRequest
from shared.presentation.api.dependencies.security import get_current_principal
from shared.presentation.api.mock_data import BASE_TIME
from shared.presentation.api.mock_data import MOCK_CHAT_ID
from shared.presentation.api.mock_data import build_chat
from shared.presentation.api.schemas.common import CursorPage

router = APIRouter(
    prefix="/workspaces/{workspace_id}/chats",
    tags=["Chats"],
    dependencies=[Depends(get_current_principal)],
)


@router.get(
    "",
    response_model=ChatListResponse,
    status_code=status.HTTP_200_OK,
    summary="Список моих чатов в воркспейсе",
)
async def list_chats(
    workspace_id: Annotated[UUID, Path()],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: Annotated[str | None, Query()] = None,
    sort: Annotated[str, Query()] = "-updated_at",
) -> ChatListResponse:
    """Return mocked personal chats for a workspace."""

    chat_payload = build_chat(workspace_id=workspace_id)

    items = [
        ChatResponse(
            id=chat_payload["id"],
            workspace_id=chat_payload["workspace_id"],
            title=chat_payload["title"],
            created_at=chat_payload["created_at"],
            updated_at=chat_payload["updated_at"],
            last_message_at=chat_payload["last_message_at"],
        ),
    ]

    return ChatListResponse(
        items=items[:limit],
        page=CursorPage(next_cursor=cursor, has_more=False),
    )


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание чата",
)
async def create_chat(
    workspace_id: Annotated[UUID, Path()],
    payload: CreateChatRequest,
) -> ChatResponse:
    """Return a mocked created chat."""

    chat_payload = build_chat(
        workspace_id=workspace_id,
        chat_id=MOCK_CHAT_ID,
        title=payload.title,
        created_at=BASE_TIME,
        updated_at=BASE_TIME,
        last_message_at=None,
    )

    return ChatResponse(
        id=chat_payload["id"],
        workspace_id=chat_payload["workspace_id"],
        title=chat_payload["title"],
        created_at=chat_payload["created_at"],
        updated_at=chat_payload["updated_at"],
        last_message_at=chat_payload["last_message_at"],
    )


@router.get(
    "/{chat_id}",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение чата",
)
async def get_chat(
    workspace_id: Annotated[UUID, Path()],
    chat_id: Annotated[UUID, Path()],
) -> ChatResponse:
    """Return a mocked chat by id."""

    chat_payload = build_chat(workspace_id=workspace_id, chat_id=chat_id)
    return ChatResponse(
        id=chat_payload["id"],
        workspace_id=chat_payload["workspace_id"],
        title=chat_payload["title"],
        created_at=chat_payload["created_at"],
        updated_at=chat_payload["updated_at"],
        last_message_at=chat_payload["last_message_at"],
    )


@router.patch(
    "/{chat_id}",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновление чата",
)
async def update_chat(
    workspace_id: Annotated[UUID, Path()],
    chat_id: Annotated[UUID, Path()],
    payload: UpdateChatRequest,
) -> ChatResponse:
    """Return a mocked updated chat."""

    chat_payload = build_chat(
        workspace_id=workspace_id,
        chat_id=chat_id,
        title=payload.title,
    )

    return ChatResponse(
        id=chat_payload["id"],
        workspace_id=chat_payload["workspace_id"],
        title=chat_payload["title"],
        created_at=chat_payload["created_at"],
        updated_at=chat_payload["updated_at"],
        last_message_at=chat_payload["last_message_at"],
    )


@router.delete(
    "/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление чата",
)
async def delete_chat(
    workspace_id: Annotated[UUID, Path()],
    chat_id: Annotated[UUID, Path()],
) -> Response:
    """Acknowledge chat deletion without body."""

    return Response(status_code=status.HTTP_204_NO_CONTENT)
