"""Message routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from messages.application.use_cases.create_message import CreateMessage
from messages.application.use_cases.create_message import (
    CreateMessageRequest as CreateMessageCommand,
)
from messages.application.use_cases.list_messages import ListMessages
from messages.application.use_cases.list_messages import (
    ListMessagesRequest,
)
from messages.domain.exceptions.message_exceptions import (
    MessageChatNotFoundError,
)
from messages.presentation.api.dependencies import (
    get_create_message_use_case,
)
from messages.presentation.api.dependencies import (
    get_list_messages_use_case,
)
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
from shared.presentation.api.dependencies.security import (
    AuthenticatedPrincipal,
)
from shared.presentation.api.dependencies.security import get_current_principal
from shared.presentation.api.schemas.common import CursorPage
from shared.presentation.api.schemas.common import DocumentContextItem
from shared.presentation.api.schemas.common import MessageContextResponse

router = APIRouter(
    prefix="/workspaces/{workspace_id}/chats/{chat_id}/messages",
    tags=["Messages"],
)


@router.get(
    "",
    response_model=MessageListResponse,
    status_code=status.HTTP_200_OK,
    summary="История сообщений",
)
async def list_messages(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        ListMessages,
        Depends(get_list_messages_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
    chat_id: Annotated[UUID, Path()],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query()] = None,
) -> MessageListResponse:
    """Return stored chat history."""
    try:
        payload = await use_case.execute(
            ListMessagesRequest(
                workspace_id=workspace_id,
                chat_id=chat_id,
                actor_user_id=principal.user_id,
                limit=limit,
                cursor=cursor,
            )
        )
    except MessageChatNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return MessageListResponse(
        items=[
            MessageResponse(
                id=item.id,
                chat_id=item.chat_id,
                role=item.role,
                content=item.content,
                status=item.status,
                created_at=item.created_at,
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
    response_model=CreateMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Отправка сообщения",
)
async def create_message(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        CreateMessage,
        Depends(get_create_message_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
    chat_id: Annotated[UUID, Path()],
    payload: CreateMessageRequest,
) -> CreateMessageResponse:
    """Persist a user message and generate an assistant reply."""
    try:
        result = await use_case.execute(
            CreateMessageCommand(
                workspace_id=workspace_id,
                chat_id=chat_id,
                actor_user_id=principal.user_id,
                content=payload.content,
            )
        )
    except MessageChatNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return CreateMessageResponse(
        user_message=MessageResponse(
            id=result.user_message.id,
            chat_id=result.user_message.chat_id,
            role=result.user_message.role,
            content=result.user_message.content,
            status=result.user_message.status,
            created_at=result.user_message.created_at,
        ),
        assistant_message=MessageResponse(
            id=result.assistant_message.id,
            chat_id=result.assistant_message.chat_id,
            role=result.assistant_message.role,
            content=result.assistant_message.content,
            status=result.assistant_message.status,
            created_at=result.assistant_message.created_at,
        ),
        context=MessageContextResponse(
            documents_used=[
                DocumentContextItem(
                    document_id=item.document_id,
                    filename=item.filename,
                )
                for item in result.context_documents
            ],
        ),
    )
