from uuid import UUID

from agentic_shared.crosscut.auth.context import AuthContext
from agentic_shared.crosscut.auth.roles import AppRole
from agentic_shared.crosscut.auth.settings import AuthSettings
from agentic_shared.frameworks.fastapi.dependencies.auth.dependency import require_roles
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException, Request, Response, status

from agentic_api.modules.documents.schemas import (
    CompleteUploadResponse,
    DocumentListResponse,
    DocumentOut,
    PresignUploadRequest,
    PresignUploadResponse,
    ReindexDocumentResponse,
)
from agentic_api.modules.documents.service import DocumentService
from agentic_api.modules.jobs.service import JobService

router = APIRouter(prefix="/documents", tags=["documents"])


def _validate_pdf_filename(filename: str) -> None:
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")


@router.get("", response_model=DocumentListResponse)
@inject
async def list_documents(
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    document_service: FromDishka[DocumentService],
) -> DocumentListResponse:
    require_roles(auth, auth_settings, AppRole.READ)
    items = await document_service.list_documents()
    return DocumentListResponse(items=items, total=len(items))


@router.get("/{document_id}", response_model=DocumentOut)
@inject
async def get_document(
    document_id: UUID,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    document_service: FromDishka[DocumentService],
) -> DocumentOut:
    require_roles(auth, auth_settings, AppRole.READ)
    out = await document_service.get_out(document_id)
    if not out:
        raise HTTPException(status_code=404, detail="Document not found")
    return out


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_document(
    document_id: UUID,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    document_service: FromDishka[DocumentService],
) -> Response:
    require_roles(auth, auth_settings, AppRole.WRITE)
    await document_service.delete_document(document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/upload/presign",
    response_model=PresignUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def presign_upload(
    body: PresignUploadRequest,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    document_service: FromDishka[DocumentService],
) -> PresignUploadResponse:
    require_roles(auth, auth_settings, AppRole.WRITE)
    _validate_pdf_filename(body.filename)
    document, expires_in = await document_service.create_upload_presign(body.filename)
    out = await document_service.get_out(document.id)
    if not out:
        raise HTTPException(status_code=500, detail="Failed to create document")
    return PresignUploadResponse(
        document=out,
        upload_url=f"/api/v1/documents/{document.id}/upload",
        expires_in=expires_in,
    )


@router.put("/{document_id}/upload", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def upload_document_bytes(
    document_id: UUID,
    request: Request,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    document_service: FromDishka[DocumentService],
) -> Response:
    require_roles(auth, auth_settings, AppRole.WRITE)
    await document_service.upload_bytes(document_id, await request.body())
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{document_id}/reindex",
    response_model=ReindexDocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@inject
async def reindex_document(
    document_id: UUID,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    document_service: FromDishka[DocumentService],
) -> ReindexDocumentResponse:
    require_roles(auth, auth_settings, AppRole.WRITE)
    document, job = await document_service.reindex_document(document_id)

    out = await document_service.get_out(document.id)
    if not out:
        raise HTTPException(status_code=500, detail="Failed to load document")
    return ReindexDocumentResponse(document=out, job_id=job.id)


@router.post(
    "/{document_id}/complete",
    response_model=CompleteUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@inject
async def complete_upload(
    document_id: UUID,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    document_service: FromDishka[DocumentService],
    job_service: FromDishka[JobService],
) -> CompleteUploadResponse:
    require_roles(auth, auth_settings, AppRole.WRITE)
    document, job = await document_service.complete_upload(document_id)

    await job_service.enqueue_index_job(job.id, document.id, document.minio_key, document.filename)
    out = await document_service.get_out(document.id)
    if not out:
        raise HTTPException(status_code=500, detail="Failed to load document")
    return CompleteUploadResponse(document=out, job_id=job.id)
