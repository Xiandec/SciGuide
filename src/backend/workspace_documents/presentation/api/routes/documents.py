"""Workspace document routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query
from fastapi import Response
from fastapi import UploadFile, status

from shared.presentation.api.dependencies.security import (
    AuthenticatedPrincipal,
)
from shared.presentation.api.dependencies.security import get_current_principal
from shared.presentation.api.schemas.common import CursorPage
from workspace_documents.application.use_cases.delete_workspace_document import (  # noqa: E501
    DeleteWorkspaceDocument,
)
from workspace_documents.application.use_cases.delete_workspace_document import (  # noqa: E501
    DeleteWorkspaceDocumentRequest,
)
from workspace_documents.application.use_cases.get_document_processing import (
    GetDocumentProcessing,
)
from workspace_documents.application.use_cases.get_document_processing import (
    GetDocumentProcessingRequest,
)
from workspace_documents.application.use_cases.get_workspace_document import (
    GetWorkspaceDocument,
)
from workspace_documents.application.use_cases.get_workspace_document import (
    GetWorkspaceDocumentRequest,
)
from workspace_documents.application.use_cases.list_workspace_documents import (  # noqa: E501
    ListWorkspaceDocuments,
)
from workspace_documents.application.use_cases.list_workspace_documents import (  # noqa: E501
    ListWorkspaceDocumentsRequest,
)
from workspace_documents.application.use_cases.upload_workspace_document import (  # noqa: E501
    UploadWorkspaceDocument,
)
from workspace_documents.application.use_cases.upload_workspace_document import (  # noqa: E501
    UploadWorkspaceDocumentRequest,
)
from workspace_documents.domain.exceptions.document_exceptions import (
    WorkspaceDocumentAccessDeniedError,
)
from workspace_documents.domain.exceptions.document_exceptions import (
    WorkspaceDocumentNotFoundError,
)
from workspace_documents.domain.exceptions.document_exceptions import (
    WorkspaceDocumentStorageError,
)
from workspace_documents.presentation.api.dependencies import (
    get_delete_workspace_document_use_case,
)
from workspace_documents.presentation.api.dependencies import (
    get_document_processing_use_case,
)
from workspace_documents.presentation.api.dependencies import (
    get_get_workspace_document_use_case,
)
from workspace_documents.presentation.api.dependencies import (
    get_list_workspace_documents_use_case,
)
from workspace_documents.presentation.api.dependencies import (
    get_upload_workspace_document_use_case,
)
from workspace_documents.presentation.api.schemas.document_schemas import (
    DocumentProcessingResponse,
)
from workspace_documents.presentation.api.schemas.document_schemas import (
    WorkspaceDocumentListResponse,
)
from workspace_documents.presentation.api.schemas.document_schemas import (
    WorkspaceDocumentResponse,
)
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceNotFoundError,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/documents",
    tags=["Workspace Documents"],
)


@router.get(
    "",
    response_model=WorkspaceDocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="Список документов воркспейса",
)
async def list_documents(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        ListWorkspaceDocuments,
        Depends(get_list_workspace_documents_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: Annotated[str | None, Query()] = None,
) -> WorkspaceDocumentListResponse:
    """Return workspace documents visible to the actor."""
    try:
        payload = await use_case.execute(
            ListWorkspaceDocumentsRequest(
                workspace_id=workspace_id,
                actor_user_id=principal.user_id,
                limit=limit,
                cursor=cursor,
            ),
        )
    except WorkspaceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return WorkspaceDocumentListResponse(
        items=[
            WorkspaceDocumentResponse(
                id=item.id,
                workspace_id=item.workspace_id,
                filename=item.filename,
                content_type=item.content_type,
                size_bytes=item.size_bytes,
                status=item.status,
                created_at=item.created_at,
                uploaded_by=item.uploaded_by,
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
    response_model=WorkspaceDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузка документа",
)
async def upload_document(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        UploadWorkspaceDocument,
        Depends(get_upload_workspace_document_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
    file: UploadFile = File(...),
    title: Annotated[str | None, Form()] = None,
) -> WorkspaceDocumentResponse:
    """Upload a document into the workspace."""
    filename = title or file.filename or "document.bin"
    content_type = file.content_type or "application/octet-stream"
    size_bytes = await _measure_upload_size(file)

    try:
        document = await use_case.execute(
            UploadWorkspaceDocumentRequest(
                workspace_id=workspace_id,
                actor_user_id=principal.user_id,
                filename=filename,
                content_type=content_type,
                size_bytes=size_bytes,
                file_stream=file.file,
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
    except WorkspaceDocumentAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except WorkspaceDocumentStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    finally:
        await file.close()

    return WorkspaceDocumentResponse(
        id=document.id,
        workspace_id=document.workspace_id,
        filename=document.filename,
        content_type=document.content_type,
        size_bytes=document.size_bytes,
        status=document.status,
        created_at=document.created_at,
        uploaded_by=document.uploaded_by,
    )


@router.get(
    "/{document_id}",
    response_model=WorkspaceDocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение документа",
)
async def get_document(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        GetWorkspaceDocument,
        Depends(get_get_workspace_document_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
    document_id: Annotated[UUID, Path()],
) -> WorkspaceDocumentResponse:
    """Return workspace document metadata."""
    try:
        document = await use_case.execute(
            GetWorkspaceDocumentRequest(
                workspace_id=workspace_id,
                document_id=document_id,
                actor_user_id=principal.user_id,
            ),
        )
    except (WorkspaceNotFoundError, WorkspaceDocumentNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return WorkspaceDocumentResponse(
        id=document.id,
        workspace_id=document.workspace_id,
        filename=document.filename,
        content_type=document.content_type,
        size_bytes=document.size_bytes,
        status=document.status,
        created_at=document.created_at,
        uploaded_by=document.uploaded_by,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление документа",
)
async def delete_document(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        DeleteWorkspaceDocument,
        Depends(get_delete_workspace_document_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
    document_id: Annotated[UUID, Path()],
) -> Response:
    """Delete a workspace document."""
    try:
        await use_case.execute(
            DeleteWorkspaceDocumentRequest(
                workspace_id=workspace_id,
                document_id=document_id,
                actor_user_id=principal.user_id,
            ),
        )
    except (WorkspaceNotFoundError, WorkspaceDocumentNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except WorkspaceDocumentAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{document_id}/processing",
    response_model=DocumentProcessingResponse,
    status_code=status.HTTP_200_OK,
    summary="Статус обработки документа",
)
async def get_document_processing(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
    use_case: Annotated[
        GetDocumentProcessing,
        Depends(get_document_processing_use_case),
    ],
    workspace_id: Annotated[UUID, Path()],
    document_id: Annotated[UUID, Path()],
) -> DocumentProcessingResponse:
    """Return current processing state for a workspace document."""
    try:
        processing_payload = await use_case.execute(
            GetDocumentProcessingRequest(
                workspace_id=workspace_id,
                document_id=document_id,
                actor_user_id=principal.user_id,
            ),
        )
    except (WorkspaceNotFoundError, WorkspaceDocumentNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return DocumentProcessingResponse(
        document_id=processing_payload.document_id,
        status=processing_payload.status,
        stage=processing_payload.stage,
        updated_at=processing_payload.updated_at,
        error=processing_payload.error,
    )


async def _measure_upload_size(file: UploadFile) -> int:
    """Measure uploaded file size without loading it into memory."""
    file.file.seek(0, 2)
    size_bytes = file.file.tell()
    file.file.seek(0)
    return size_bytes
