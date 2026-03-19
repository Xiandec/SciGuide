"""Mock workspace document routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Path, Query, Response
from fastapi import UploadFile, status

from shared.presentation.api.dependencies.security import get_current_principal
from shared.presentation.api.mock_data import BASE_TIME
from shared.presentation.api.mock_data import MOCK_DOCUMENT_ID
from shared.presentation.api.mock_data import build_document
from shared.presentation.api.mock_data import build_processing_status
from shared.presentation.api.schemas.common import CursorPage
from workspace_documents.presentation.api.schemas.document_schemas import (
    DocumentProcessingResponse,
)
from workspace_documents.presentation.api.schemas.document_schemas import (
    WorkspaceDocumentListResponse,
)
from workspace_documents.presentation.api.schemas.document_schemas import (
    WorkspaceDocumentResponse,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/documents",
    tags=["Workspace Documents"],
    dependencies=[Depends(get_current_principal)],
)


@router.get(
    "",
    response_model=WorkspaceDocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="Список документов воркспейса",
)
async def list_documents(
    workspace_id: Annotated[UUID, Path()],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: Annotated[str | None, Query()] = None,
) -> WorkspaceDocumentListResponse:
    """Return mocked workspace documents."""

    document_payload = build_document(workspace_id=workspace_id)

    items = [
        WorkspaceDocumentResponse(
            id=document_payload["id"],
            workspace_id=document_payload["workspace_id"],
            filename=document_payload["filename"],
            content_type=document_payload["content_type"],
            size_bytes=document_payload["size_bytes"],
            status=document_payload["status"],
            created_at=document_payload["created_at"],
            uploaded_by=document_payload["uploaded_by"],
        ),
    ]

    return WorkspaceDocumentListResponse(
        items=items[:limit],
        page=CursorPage(next_cursor=cursor, has_more=False),
    )


@router.post(
    "",
    response_model=WorkspaceDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузка документа",
)
async def upload_document(
    workspace_id: Annotated[UUID, Path()],
    file: UploadFile = File(...),
    title: Annotated[str | None, Form()] = None,
) -> WorkspaceDocumentResponse:
    """Return a mocked uploaded document payload."""

    filename = title or file.filename or "document.bin"
    content_type = file.content_type or "application/octet-stream"

    document_payload = build_document(
        workspace_id=workspace_id,
        document_id=MOCK_DOCUMENT_ID,
        filename=filename,
        content_type=content_type,
        status="uploaded",
        created_at=BASE_TIME,
    )

    return WorkspaceDocumentResponse(
        id=document_payload["id"],
        workspace_id=document_payload["workspace_id"],
        filename=document_payload["filename"],
        content_type=document_payload["content_type"],
        size_bytes=document_payload["size_bytes"],
        status=document_payload["status"],
        created_at=document_payload["created_at"],
        uploaded_by=document_payload["uploaded_by"],
    )


@router.get(
    "/{document_id}",
    response_model=WorkspaceDocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение документа",
)
async def get_document(
    workspace_id: Annotated[UUID, Path()],
    document_id: Annotated[UUID, Path()],
) -> WorkspaceDocumentResponse:
    """Return a mocked workspace document by id."""

    document_payload = build_document(
        workspace_id=workspace_id,
        document_id=document_id,
    )

    return WorkspaceDocumentResponse(
        id=document_payload["id"],
        workspace_id=document_payload["workspace_id"],
        filename=document_payload["filename"],
        content_type=document_payload["content_type"],
        size_bytes=document_payload["size_bytes"],
        status=document_payload["status"],
        created_at=document_payload["created_at"],
        uploaded_by=document_payload["uploaded_by"],
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление документа",
)
async def delete_document(
    workspace_id: Annotated[UUID, Path()],
    document_id: Annotated[UUID, Path()],
) -> Response:
    """Acknowledge document deletion without body."""

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{document_id}/processing",
    response_model=DocumentProcessingResponse,
    status_code=status.HTTP_200_OK,
    summary="Статус обработки документа",
)
async def get_document_processing(
    workspace_id: Annotated[UUID, Path()],
    document_id: Annotated[UUID, Path()],
) -> DocumentProcessingResponse:
    """Return a mocked processing status."""

    processing_payload = build_processing_status(document_id=document_id)
    return DocumentProcessingResponse(
        document_id=processing_payload["document_id"],
        status=processing_payload["status"],
        stage=processing_payload["stage"],
        updated_at=processing_payload["updated_at"],
        error=processing_payload["error"],
    )
