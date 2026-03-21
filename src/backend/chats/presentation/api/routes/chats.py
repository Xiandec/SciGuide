"""Chat routes."""

from __future__ import annotations

from typing import Annotated
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from fastapi import status

from chats.application.use_cases.create_chat import CreateChat
from chats.application.use_cases.create_chat import (
    CreateChatRequest as CreateChatCommand,
)
from chats.application.use_cases.delete_chat import DeleteChat
from chats.application.use_cases.delete_chat import DeleteChatRequest
from chats.application.use_cases.get_chat import GetChat
from chats.application.use_cases.get_chat import GetChatRequest
from chats.application.use_cases.list_chats import ListChats
from chats.application.use_cases.list_chats import ListChatsRequest
from chats.application.use_cases.update_chat import UpdateChat
from chats.application.use_cases.update_chat import (
    UpdateChatRequest as UpdateChatCommand,
)
from chats.domain.exceptions.chat_exceptions import ChatNotFoundError
from chats.presentation.api.dependencies import get_create_chat_use_case
from chats.presentation.api.dependencies import get_delete_chat_use_case
from chats.presentation.api.dependencies import get_get_chat_use_case
from chats.presentation.api.dependencies import get_list_chats_use_case
from chats.presentation.api.dependencies import get_update_chat_use_case
from chats.presentation.api.schemas.chat_schemas import ChatListResponse
from chats.presentation.api.schemas.chat_schemas import ChatResponse
from chats.presentation.api.schemas.chat_schemas import CreateChatRequest
from chats.presentation.api.schemas.chat_schemas import UpdateChatRequest
from shared.presentation.api.dependencies.security import (
    AuthenticatedPrincipal,
)
from shared.presentation.api.dependencies.security import get_current_principal
from shared.presentation.api.schemas.common import CursorPage
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceNotFoundError,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/chats",
    tags=["Chats"],
)


@router.get(
    "",
    response_model=ChatListResponse,
    status_code=status.HTTP_200_OK,
    summary="Список моих чатов в воркспейсе",
)
async def list_chats(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        ListChats,
        Depends(get_list_chats_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: Annotated[str | None, Query()] = None,
    sort: Annotated[
        Literal["-updated_at", "updated_at"],
        Query(),
    ] = "-updated_at",
) -> ChatListResponse:
    """Return personal chats for an accessible workspace."""
    try:
        payload = await use_case.execute(
            ListChatsRequest(
                workspace_id=workspace_id,
                actor_user_id=principal.user_id,
                limit=limit,
                cursor=cursor,
                sort=sort,
            ),
        )
    except WorkspaceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ChatListResponse(
        items=[
            ChatResponse(
                id=item.id,
                workspace_id=item.workspace_id,
                title=item.title,
                created_at=item.created_at,
                updated_at=item.updated_at,
                last_message_at=item.last_message_at,
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
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание чата",
)
async def create_chat(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        CreateChat,
        Depends(get_create_chat_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
    payload: CreateChatRequest,
) -> ChatResponse:
    """Create a personal chat."""
    try:
        chat = await use_case.execute(
            CreateChatCommand(
                workspace_id=workspace_id,
                actor_user_id=principal.user_id,
                title=payload.title,
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except WorkspaceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ChatResponse(
        id=chat.id,
        workspace_id=chat.workspace_id,
        title=chat.title,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        last_message_at=chat.last_message_at,
    )


@router.get(
    "/{chat_id}",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение чата",
)
async def get_chat(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        GetChat,
        Depends(get_get_chat_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
    chat_id: Annotated[UUID, Path()],
) -> ChatResponse:
    """Return a personal chat by id."""
    try:
        chat = await use_case.execute(
            GetChatRequest(
                workspace_id=workspace_id,
                chat_id=chat_id,
                actor_user_id=principal.user_id,
            ),
        )
    except (WorkspaceNotFoundError, ChatNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ChatResponse(
        id=chat.id,
        workspace_id=chat.workspace_id,
        title=chat.title,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        last_message_at=chat.last_message_at,
    )


@router.patch(
    "/{chat_id}",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновление чата",
)
async def update_chat(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        UpdateChat,
        Depends(get_update_chat_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
    chat_id: Annotated[UUID, Path()],
    payload: UpdateChatRequest,
) -> ChatResponse:
    """Update a personal chat."""
    try:
        chat = await use_case.execute(
            UpdateChatCommand(
                workspace_id=workspace_id,
                chat_id=chat_id,
                actor_user_id=principal.user_id,
                title=payload.title,
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except (WorkspaceNotFoundError, ChatNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ChatResponse(
        id=chat.id,
        workspace_id=chat.workspace_id,
        title=chat.title,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        last_message_at=chat.last_message_at,
    )


@router.delete(
    "/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление чата",
)
async def delete_chat(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        DeleteChat,
        Depends(get_delete_chat_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
    chat_id: Annotated[UUID, Path()],
) -> Response:
    """Delete a personal chat."""
    try:
        await use_case.execute(
            DeleteChatRequest(
                workspace_id=workspace_id,
                chat_id=chat_id,
                actor_user_id=principal.user_id,
            ),
        )
    except (WorkspaceNotFoundError, ChatNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
