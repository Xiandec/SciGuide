"""Reusable mock payload factories for API presentation layer."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

MOCK_USER_ID = UUID("2f3c5a89-4d55-4c34-98d8-95dbe6c50c31")
MOCK_MEMBER_USER_ID = UUID("9b41e2d1-0c4b-40db-b80b-6bba9e6cd18e")
MOCK_WORKSPACE_ID = UUID("06cf3b57-6707-4834-bd43-7c120e08f4e4")
MOCK_CREATED_WORKSPACE_ID = UUID("ab1f8d19-a1b8-4fe7-a761-0a3f9fd7e7f2")
MOCK_DOCUMENT_ID = UUID("d86f4fc7-6a6f-40a0-ae97-3df5c647d0d9")
MOCK_CHAT_ID = UUID("0ee04eaf-8a5a-4c1f-857e-0ef8f48d31b4")
MOCK_USER_MESSAGE_ID = UUID("4b4f87ef-7c16-4617-88f2-7f9448aa2c0d")
MOCK_ASSISTANT_MESSAGE_ID = UUID("9d2df75e-4cb9-452d-8576-9c3ba104d49e")

MOCK_USER_EMAIL = "user@example.com"
MOCK_USER_DISPLAY_NAME = "Ivan Petrov"
MOCK_ACCESS_TOKEN = "mock-access-token"
MOCK_REFRESH_TOKEN = "mock-refresh-token"

BASE_TIME = datetime(2026, 3, 19, 10, 15, 30, tzinfo=timezone.utc)
UPDATED_TIME = datetime(2026, 3, 19, 10, 16, 10, tzinfo=timezone.utc)
ASSISTANT_TIME = datetime(2026, 3, 19, 10, 16, 12, tzinfo=timezone.utc)


def build_user_summary() -> dict[str, object]:
    """Return the stable mock user profile."""

    return {
        "id": MOCK_USER_ID,
        "email": MOCK_USER_EMAIL,
        "display_name": MOCK_USER_DISPLAY_NAME,
    }


def build_workspace(
    workspace_id: UUID = MOCK_WORKSPACE_ID,
    *,
    name: str = "Cardiology",
    description: str = "Scientific workspace for cardiology materials",
    workspace_type: str = "private",
    access_mode: str = "owner_only",
    my_role: str = "admin",
    created_at: datetime = BASE_TIME,
    updated_at: datetime = BASE_TIME,
) -> dict[str, object]:
    """Return a mock workspace payload."""

    return {
        "id": workspace_id,
        "name": name,
        "description": description,
        "type": workspace_type,
        "access_mode": access_mode,
        "my_role": my_role,
        "created_at": created_at,
        "updated_at": updated_at,
    }


def build_member(
    user_id: UUID = MOCK_USER_ID,
    *,
    email: str = MOCK_USER_EMAIL,
    display_name: str = MOCK_USER_DISPLAY_NAME,
    role: str = "admin",
    joined_at: datetime = BASE_TIME,
) -> dict[str, object]:
    """Return a mock workspace member payload."""

    return {
        "user_id": user_id,
        "email": email,
        "display_name": display_name,
        "role": role,
        "joined_at": joined_at,
    }


def build_prompt(workspace_id: UUID = MOCK_WORKSPACE_ID) -> dict[str, object]:
    """Return a mock workspace prompt payload."""

    return {
        "workspace_id": workspace_id,
        "content": "You are a scientific assistant specialized in cardiology.",
        "updated_at": BASE_TIME,
        "updated_by": MOCK_USER_ID,
    }


def build_document(
    workspace_id: UUID = MOCK_WORKSPACE_ID,
    document_id: UUID = MOCK_DOCUMENT_ID,
    *,
    filename: str = "paper.pdf",
    content_type: str = "application/pdf",
    size_bytes: int = 2_481_901,
    status: str = "processed",
    created_at: datetime = BASE_TIME,
    uploaded_by: UUID = MOCK_USER_ID,
) -> dict[str, object]:
    """Return a mock document payload."""

    return {
        "id": document_id,
        "workspace_id": workspace_id,
        "filename": filename,
        "content_type": content_type,
        "size_bytes": size_bytes,
        "status": status,
        "created_at": created_at,
        "uploaded_by": uploaded_by,
    }


def build_processing_status(
    document_id: UUID = MOCK_DOCUMENT_ID,
    *,
    status: str = "processing",
    stage: str = "embedding",
    updated_at: datetime = BASE_TIME,
    error: str | None = None,
) -> dict[str, object]:
    """Return a mock document processing payload."""

    return {
        "document_id": document_id,
        "status": status,
        "stage": stage,
        "updated_at": updated_at,
        "error": error,
    }


def build_chat(
    workspace_id: UUID = MOCK_WORKSPACE_ID,
    chat_id: UUID = MOCK_CHAT_ID,
    *,
    title: str = "Methods discussion",
    created_at: datetime = BASE_TIME,
    updated_at: datetime = UPDATED_TIME,
    last_message_at: datetime | None = UPDATED_TIME,
) -> dict[str, object]:
    """Return a mock chat payload."""

    return {
        "id": chat_id,
        "workspace_id": workspace_id,
        "title": title,
        "created_at": created_at,
        "updated_at": updated_at,
        "last_message_at": last_message_at,
    }


def build_message(
    chat_id: UUID = MOCK_CHAT_ID,
    message_id: UUID = MOCK_USER_MESSAGE_ID,
    *,
    role: str = "user",
    content: str = "Explain graph-guided retrieval.",
    status: str = "completed",
    created_at: datetime = UPDATED_TIME,
) -> dict[str, object]:
    """Return a mock message payload."""

    return {
        "id": message_id,
        "chat_id": chat_id,
        "role": role,
        "content": content,
        "status": status,
        "created_at": created_at,
    }
