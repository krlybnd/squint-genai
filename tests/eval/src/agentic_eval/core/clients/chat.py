"""Chat HTTP facade: generated OpenAPI client plus SSE frame parsing."""

from __future__ import annotations

from uuid import UUID

import httpx
from agentic_chat_client import Client
from agentic_chat_client.api.chat.create_session_v1_chat_sessions_post import (
    asyncio as create_session,
)
from agentic_chat_client.api.chat.delete_session_v1_chat_sessions_session_id_delete import (
    asyncio as delete_session,
)
from agentic_chat_client.api.chat.stream_chat_v1_chat_sessions_session_id_stream_post import (
    asyncio as stream_chat,
)
from agentic_chat_client.api.health.ready_ready_get import asyncio as chat_ready
from agentic_chat_client.errors import UnexpectedStatus
from agentic_chat_client.models.chat_session_out import ChatSessionOut
from agentic_chat_client.models.chat_stream_request import ChatStreamRequest
from agentic_chat_client.models.create_session_request import CreateSessionRequest

from agentic_eval.core.clients.sse import SseEvent, parse_sse
from agentic_eval.core.clients.transport import client_kwargs

_HTTP = (httpx.HTTPError, UnexpectedStatus)


class ChatHttp:
    """Composes ``agentic_chat_client.Client``; adds stream frame parsing the generator omits."""

    def __init__(self, base_url: str, *, headers: dict[str, str], max_connections: int) -> None:
        self._client = Client(
            **client_kwargs(base_url, headers=headers, max_connections=max_connections)
        )

    async def __aenter__(self) -> ChatHttp:
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self._client.__aexit__(*_exc)

    async def ready(self) -> None:
        try:
            await chat_ready(client=self._client)
        except _HTTP as exc:
            raise RuntimeError(f"chat not ready: {exc}") from exc

    async def create_session(self, *, title: str) -> UUID:
        created = await create_session(client=self._client, body=CreateSessionRequest(title=title))
        if not isinstance(created, ChatSessionOut):
            raise RuntimeError(f"create chat session failed: {created}")
        return created.id

    async def delete_session(self, session_id: UUID) -> None:
        try:
            await delete_session(session_id, client=self._client)
        except _HTTP:
            pass

    async def stream(self, session_id: UUID, message: str) -> list[SseEvent]:
        try:
            raw = await stream_chat(
                session_id, client=self._client, body=ChatStreamRequest(message=message)
            )
        except _HTTP as exc:
            raise RuntimeError(f"chat stream failed: {exc}") from exc
        if not isinstance(raw, str) or not raw:
            raise RuntimeError(f"chat stream failed: {raw}")
        return parse_sse(raw)
