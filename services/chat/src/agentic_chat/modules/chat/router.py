from collections.abc import AsyncIterator
from uuid import UUID

from agentic_shared.crosscut.auth.context import AuthContext
from agentic_shared.crosscut.auth.roles import AppRole
from agentic_shared.crosscut.auth.settings import AuthSettings
from agentic_shared.crosscut.i18n import resolve_locale
from agentic_shared.frameworks.fastapi.dependencies.auth.dependency import require_roles
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Request, Response, status
from sse_starlette.sse import EventSourceResponse

from agentic_chat.modules.chat.schemas import (
    ChatMessageOut,
    ChatReplayRequest,
    ChatSessionOut,
    ChatStreamRequest,
    CreateSessionRequest,
)
from agentic_chat.modules.chat.service import ChatService
from agentic_chat.modules.chat.streaming.sse_events import (
    SSE_OPENAPI_SUCCESS,
    parse_sse_chunk,
)
from agentic_chat.modules.chat.streaming.stream_service import ChatStreamService

router = APIRouter(prefix="/v1/chat", tags=["chat"])


def _sse_response(stream: AsyncIterator[str]) -> EventSourceResponse:
    async def event_generator():
        async for chunk in stream:
            yield parse_sse_chunk(chunk)

    return EventSourceResponse(event_generator())


@router.get("/sessions", response_model=list[ChatSessionOut])
@inject
async def list_sessions(
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    chat_service: FromDishka[ChatService],
) -> list[ChatSessionOut]:
    require_roles(auth, auth_settings, AppRole.READ)
    return await chat_service.list_sessions()


@router.post("/sessions", response_model=ChatSessionOut, status_code=201)
@inject
async def create_session(
    body: CreateSessionRequest,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    chat_service: FromDishka[ChatService],
) -> ChatSessionOut:
    require_roles(auth, auth_settings, AppRole.WRITE)
    return await chat_service.create_session(body.title)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_session(
    session_id: UUID,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    chat_service: FromDishka[ChatService],
) -> Response:
    require_roles(auth, auth_settings, AppRole.WRITE)
    await chat_service.delete_session(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
@inject
async def get_messages(
    session_id: UUID,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    chat_service: FromDishka[ChatService],
) -> list[ChatMessageOut]:
    require_roles(auth, auth_settings, AppRole.READ)
    return await chat_service.get_messages(session_id)


@router.delete(
    "/sessions/{session_id}/messages/{message_id}/tail",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def truncate_messages(
    session_id: UUID,
    message_id: UUID,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    chat_service: FromDishka[ChatService],
) -> Response:
    require_roles(auth, auth_settings, AppRole.WRITE)
    await chat_service.truncate_messages_from(session_id, message_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/sessions/{session_id}/stream",
    response_class=EventSourceResponse,
    responses=SSE_OPENAPI_SUCCESS,
)
@inject
async def stream_chat(
    session_id: UUID,
    body: ChatStreamRequest,
    request: Request,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    stream_service: FromDishka[ChatStreamService],
) -> EventSourceResponse:
    require_roles(auth, auth_settings, AppRole.WRITE)
    locale = resolve_locale(request.headers.get("accept-language"))
    return _sse_response(
        stream_service.stream_response(session_id, body.message, body.run_id, locale=locale),
    )


@router.post(
    "/sessions/{session_id}/replay",
    response_class=EventSourceResponse,
    responses=SSE_OPENAPI_SUCCESS,
)
@inject
async def replay_chat(
    session_id: UUID,
    body: ChatReplayRequest,
    request: Request,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    stream_service: FromDishka[ChatStreamService],
) -> EventSourceResponse:
    require_roles(auth, auth_settings, AppRole.WRITE)
    locale = resolve_locale(request.headers.get("accept-language"))
    return _sse_response(
        stream_service.stream_replay(
            session_id,
            body.run_id,
            body.query,
            body.checkpoint_id,
            locale=locale,
        ),
    )
