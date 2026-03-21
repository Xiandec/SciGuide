"""Application API router composition."""

from fastapi import APIRouter

from auth.presentation.api.routes.auth import router as auth_router
from chats.presentation.api.routes.chats import router as chats_router
from messages.presentation.api.routes.messages import router as messages_router
from workspace_documents.presentation.api.routes.documents import (
    router as documents_router,
)
from workspace_members.presentation.api.routes.members import (
    router as members_router,
)
from workspace_prompt.presentation.api.routes.prompt import (
    router as prompt_router,
)
from workspaces.presentation.api.routes.workspaces import (
    router as workspaces_router,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(workspaces_router)
api_router.include_router(members_router)
api_router.include_router(prompt_router)
api_router.include_router(documents_router)
api_router.include_router(chats_router)
api_router.include_router(messages_router)

__all__ = ["api_router"]
