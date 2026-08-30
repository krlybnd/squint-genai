from agentic_shared.crosscut.auth.context import AuthContext
from agentic_shared.crosscut.auth.roles import AppRole
from agentic_shared.crosscut.auth.settings import AuthSettings
from agentic_shared.crosscut.auth.tenant import resolve_tenant_id
from agentic_shared.frameworks.fastapi.dependencies.auth.dependency import require_roles
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter

from agentic_api.modules.retrieval.schemas import (
    CitationOut,
    DocumentChunksResponse,
    IndexedDocumentOut,
    SearchRequest,
    SearchResponse,
)
from agentic_api.modules.retrieval.service import RetrievalApiService

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/search", response_model=SearchResponse)
@inject
async def search_documents(
    body: SearchRequest,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[RetrievalApiService],
) -> SearchResponse:
    require_roles(auth, auth_settings, AppRole.READ)
    tenant_id = resolve_tenant_id(auth)
    return await service.search(body.query, top_k=body.top_k, tenant_id=tenant_id)


@router.get("/sources/{chunk_id}", response_model=CitationOut)
@inject
async def get_source_citation(
    chunk_id: str,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[RetrievalApiService],
) -> CitationOut:
    require_roles(auth, auth_settings, AppRole.READ)
    return await service.citation(chunk_id, tenant_id=resolve_tenant_id(auth))


@router.get("/indexed-documents", response_model=list[IndexedDocumentOut])
@inject
async def list_indexed_documents(
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[RetrievalApiService],
) -> list[IndexedDocumentOut]:
    require_roles(auth, auth_settings, AppRole.READ)
    return await service.list_indexed(tenant_id=resolve_tenant_id(auth))


@router.get("/documents/{doc_id}/chunks", response_model=DocumentChunksResponse)
@inject
async def list_document_chunks(
    doc_id: str,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[RetrievalApiService],
) -> DocumentChunksResponse:
    require_roles(auth, auth_settings, AppRole.READ)
    return await service.document_chunks(doc_id, tenant_id=resolve_tenant_id(auth))


@router.get("/documents/by-source/{source_file}/chunks", response_model=DocumentChunksResponse)
@inject
async def list_source_file_chunks(
    source_file: str,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[RetrievalApiService],
) -> DocumentChunksResponse:
    require_roles(auth, auth_settings, AppRole.READ)
    return await service.source_file_chunks(source_file, tenant_id=resolve_tenant_id(auth))
