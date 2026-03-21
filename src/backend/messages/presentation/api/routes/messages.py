"""Mock message routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status

from messages.presentation.api.schemas.message_schemas import (
    CreateMessageRequest,
)
from messages.presentation.api.schemas.message_schemas import (
    CreateMessageResponse,
)
from messages.presentation.api.schemas.message_schemas import (
    MessageListResponse,
)
from messages.presentation.api.schemas.message_schemas import MessageResponse
from shared.presentation.api.dependencies.security import get_current_principal
from shared.presentation.api.mock_data import ASSISTANT_TIME
from shared.presentation.api.mock_data import MOCK_ASSISTANT_MESSAGE_ID
from shared.presentation.api.mock_data import MOCK_DOCUMENT_ID
from shared.presentation.api.mock_data import MOCK_USER_MESSAGE_ID
from shared.presentation.api.mock_data import UPDATED_TIME
from shared.presentation.api.mock_data import build_message
from shared.presentation.api.schemas.common import CursorPage
from shared.presentation.api.schemas.common import DocumentContextItem
from shared.presentation.api.schemas.common import MessageContextResponse

router = APIRouter(
    prefix="/workspaces/{workspace_id}/chats/{chat_id}/messages",
    tags=["Messages"],
    dependencies=[Depends(get_current_principal)],
)


@router.get(
    "",
    response_model=MessageListResponse,
    status_code=status.HTTP_200_OK,
    summary="История сообщений",
)
async def list_messages(
    workspace_id: Annotated[UUID, Path()],
    chat_id: Annotated[UUID, Path()],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query()] = None,
) -> MessageListResponse:
    """Return mocked chat history."""

    user_message_payload = build_message(chat_id=chat_id)
    assistant_message_payload = build_message(
        chat_id=chat_id,
        message_id=MOCK_ASSISTANT_MESSAGE_ID,
        role="assistant",
        content=(
            "Graph-guided retrieval combines semantic similarity "
            "with structural signals from a concept graph."
        ),
        created_at=ASSISTANT_TIME,
    )

    items = [
        MessageResponse(
            id=user_message_payload["id"],
            chat_id=user_message_payload["chat_id"],
            role=user_message_payload["role"],
            content=user_message_payload["content"],
            status=user_message_payload["status"],
            created_at=user_message_payload["created_at"],
        ),
        MessageResponse(
            id=assistant_message_payload["id"],
            chat_id=assistant_message_payload["chat_id"],
            role=assistant_message_payload["role"],
            content=assistant_message_payload["content"],
            status=assistant_message_payload["status"],
            created_at=assistant_message_payload["created_at"],
        ),
    ]

    return MessageListResponse(
        items=items[:limit],
        page=CursorPage(next_cursor=cursor, has_more=False),
    )


@router.post(
    "",
    response_model=CreateMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Отправка сообщения",
)
async def create_message(
    workspace_id: Annotated[UUID, Path()],
    chat_id: Annotated[UUID, Path()],
    payload: CreateMessageRequest,
) -> CreateMessageResponse:
    """Return mocked saved user and assistant messages."""

    user_message_payload = build_message(
        chat_id=chat_id,
        message_id=MOCK_USER_MESSAGE_ID,
        role="user",
        content=payload.content,
        created_at=UPDATED_TIME,
    )
    assistant_message_payload = build_message(
        chat_id=chat_id,
        message_id=MOCK_ASSISTANT_MESSAGE_ID,
        role="assistant",
        content=(
            "Graph-guided retrieval combines semantic similarity "
            "with structural signals from a concept graph."
        ),
        created_at=ASSISTANT_TIME,
    )

    return CreateMessageResponse(
        user_message=MessageResponse(
            id=user_message_payload["id"],
            chat_id=user_message_payload["chat_id"],
            role=user_message_payload["role"],
            content=user_message_payload["content"],
            status=user_message_payload["status"],
            created_at=user_message_payload["created_at"],
        ),
        assistant_message=MessageResponse(
            id=assistant_message_payload["id"],
            chat_id=assistant_message_payload["chat_id"],
            role=assistant_message_payload["role"],
            content=assistant_message_payload["content"],
            status=assistant_message_payload["status"],
            created_at=assistant_message_payload["created_at"],
        ),
        context=MessageContextResponse(
            documents_used=[
                DocumentContextItem(
                    document_id=MOCK_DOCUMENT_ID,
                    filename="paper.pdf",
                ),
            ],
        ),
    )
