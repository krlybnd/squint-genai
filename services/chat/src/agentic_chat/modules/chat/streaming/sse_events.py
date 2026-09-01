"""Typed chat SSE payloads (wire format aligned with frontend StreamEvent)."""

from __future__ import annotations

import json
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field

from agentic_chat.core.state import PiiDetailState
from agentic_chat.modules.chat.enums import ReasoningStatus, ReasoningStep, SseEventType

SSE_MEDIA_TYPE = "text/event-stream"
SSE_OPENAPI_SUCCESS: dict[int | str, dict[str, Any]] = {
    200: {
        "description": (
            "Server-Sent Events. Each frame is `event: <name>` and `data: <json>`, "
            "where name is run, reasoning, status, token, session, done, or error, "
            "and data matches the corresponding *EventData model."
        ),
        "content": {
            SSE_MEDIA_TYPE: {
                "schema": {"type": "string"},
            }
        },
    }
}

__all__ = [
    "DoneEventData",
    "ErrorEventData",
    "ReasoningEventData",
    "ReasoningStatus",
    "ReasoningStep",
    "RunEventData",
    "SSE_MEDIA_TYPE",
    "SSE_OPENAPI_SUCCESS",
    "SessionEventData",
    "SseEventType",
    "StatusEventData",
    "TokenEventData",
    "format_sse_event",
    "parse_sse_chunk",
    "sse_done",
    "sse_error",
    "sse_reasoning",
    "sse_run",
    "sse_session",
    "sse_status",
    "sse_token",
]


class ReasoningEventData(BaseModel):
    step: ReasoningStep
    message: str
    status: ReasoningStatus
    chunks: int | None = None
    pii_redactions: int | None = None
    pii_details: list[PiiDetailState] | None = None
    safe_query: str | None = None
    checkpoint_id: str | None = None
    needs_retrieval: bool | None = None
    search_query: str | None = None
    rewrite_reason: str | None = None
    indexed_document_count: int | None = None
    search_meta: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid")

    def with_checkpoint(self, checkpoint_id: str | None) -> Self:
        if not checkpoint_id:
            return self
        return self.model_copy(update={"checkpoint_id": checkpoint_id})


class RunEventData(BaseModel):
    run_id: str
    replay: bool | None = None
    checkpoint_id: str | None = None

    model_config = ConfigDict(extra="forbid")


class StatusEventData(BaseModel):
    step: ReasoningStep
    chunks: int | None = None

    model_config = ConfigDict(extra="forbid")


class TokenEventData(BaseModel):
    content: str

    model_config = ConfigDict(extra="forbid")


class SessionEventData(BaseModel):
    session_id: str
    title: str

    model_config = ConfigDict(extra="forbid")


class DoneEventData(BaseModel):
    answer: str
    citations: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ErrorEventData(BaseModel):
    message: str

    model_config = ConfigDict(extra="forbid")


def format_sse_event(event: SseEventType, data: BaseModel) -> str:
    payload = data.model_dump(mode="json", exclude_none=True)
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def parse_sse_chunk(chunk: str) -> dict[str, str]:
    lines = chunk.strip().split("\n")
    event_type = "message"
    data = ""
    for line in lines:
        if line.startswith("event:"):
            event_type = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data = line.split(":", 1)[1].strip()
    return {"event": event_type, "data": data}


def sse_run(data: RunEventData) -> str:
    return format_sse_event(SseEventType.RUN, data)


def sse_reasoning(data: ReasoningEventData) -> str:
    return format_sse_event(SseEventType.REASONING, data)


def sse_status(data: StatusEventData) -> str:
    return format_sse_event(SseEventType.STATUS, data)


def sse_token(data: TokenEventData) -> str:
    return format_sse_event(SseEventType.TOKEN, data)


def sse_session(data: SessionEventData) -> str:
    return format_sse_event(SseEventType.SESSION, data)


def sse_done(data: DoneEventData) -> str:
    return format_sse_event(SseEventType.DONE, data)


def sse_error(data: ErrorEventData) -> str:
    return format_sse_event(SseEventType.ERROR, data)
