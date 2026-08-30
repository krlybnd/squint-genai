from __future__ import annotations

from typing import TypedDict, cast

from agentic_shared.crosscut.i18n import DEFAULT_LOCALE
from agentic_shared.domains.retrieval.models import ChunkPointPayload
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, ConfigDict, Field


class CommentGraphInputState(TypedDict):
    """Initial comment graph state keys (dict form after ``CommentGraphInput.as_state()``)."""

    chunk_id: str
    selected_text: str
    comment_text: str
    user_id: str | None
    chunk_payload: ChunkPointPayload
    tenant_id: str
    locale: str


class CommentGraphInput(BaseModel):
    """Validated input for the comment moderation graph (`ainvoke`)."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=1)
    selected_text: str = Field(min_length=1)
    comment_text: str = Field(min_length=2, max_length=2000)
    user_id: str | None = None
    chunk_payload: ChunkPointPayload
    tenant_id: str = Field(min_length=1)
    locale: str = DEFAULT_LOCALE

    def as_state(self) -> CommentGraphInputState:
        return cast(CommentGraphInputState, self.model_dump(mode="python"))


class CommentState(CommentGraphInputState, total=False):
    approved: bool
    rejection_reason: str
    comment_id: str
    moderation_notes: str


class CommentStateUpdate(TypedDict, total=False):
    approved: bool
    rejection_reason: str
    comment_id: str
    moderation_notes: str


CommentCompiledGraph = CompiledStateGraph[
    CommentState,
    None,
    CommentGraphInputState,
    CommentState,
]
