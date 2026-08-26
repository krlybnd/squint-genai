from agentic_shared.core.auth.context import AuthContext
from agentic_shared.core.auth.roles import AppRole
from agentic_shared.core.auth.settings import AuthSettings
from agentic_shared.core.i18n import resolve_locale
from agentic_shared.frameworks.fastapi.auth.dependencies import require_roles
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException, Request

from agentic_api.modules.annotations.schemas import (
    ChunkCommentOut,
    CreateChunkCommentRequest,
)
from agentic_api.modules.annotations.service import AnnotationService, CommentRejectedError

router = APIRouter(prefix="/annotations", tags=["annotations"])


@router.get("/chunks/{chunk_id}/comments", response_model=list[ChunkCommentOut])
@inject
async def list_chunk_comments(
    chunk_id: str,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[AnnotationService],
) -> list[ChunkCommentOut]:
    require_roles(auth, auth_settings, AppRole.READ)
    return service.list_chunk_comments(chunk_id)


@router.post("/chunks/{chunk_id}/comments", response_model=ChunkCommentOut)
@inject
async def create_chunk_comment(
    chunk_id: str,
    body: CreateChunkCommentRequest,
    request: Request,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[AnnotationService],
) -> ChunkCommentOut:
    require_roles(auth, auth_settings, AppRole.WRITE)
    locale = resolve_locale(request.headers.get("accept-language"))
    try:
        return await service.create_chunk_comment(
            chunk_id,
            body,
            user_id=auth.user_id,
            locale=locale,
        )
    except CommentRejectedError as exc:
        raise HTTPException(
            status_code=422,
            detail={"rejection_reason": exc.reason},
        ) from exc
