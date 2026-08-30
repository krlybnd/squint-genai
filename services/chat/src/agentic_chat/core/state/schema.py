from __future__ import annotations

from typing import Any, TypedDict, cast

from agentic_shared.crosscut.i18n import DEFAULT_LOCALE
from agentic_shared.domains.chat.roles import ChatMessageRole
from agentic_shared.domains.retrieval.models import ChunkCitation, SearchMeta
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, ConfigDict, Field


class GraphMessage(BaseModel):
    """Validated chat message for graph input."""

    model_config = ConfigDict(extra="forbid")

    role: ChatMessageRole
    content: str


class GraphMessageState(TypedDict):
    role: ChatMessageRole
    content: str


def graph_message(role: ChatMessageRole | str, content: str) -> GraphMessage:
    """Map persisted role strings to graph input messages."""
    normalized = role if isinstance(role, ChatMessageRole) else ChatMessageRole.from_stored(role)
    return GraphMessage(role=normalized, content=content)


class PiiDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    placeholder: str

    def as_state(self) -> PiiDetailState:
        return cast(PiiDetailState, self.model_dump(mode="python"))


class PiiDetailState(TypedDict):
    kind: str
    placeholder: str


class AgentGraphInputState(TypedDict):
    """Initial LangGraph state keys (dict form after ``AgentGraphInput.as_state()``)."""

    messages: list[GraphMessageState]
    thread_id: str
    locale: str
    tenant_id: str


class AgentGraphInput(BaseModel):
    """Validated input for a new chat graph run (`astream` / `ainvoke`)."""

    model_config = ConfigDict(extra="forbid")

    messages: list[GraphMessage] = Field(min_length=1)
    thread_id: str = Field(min_length=1)
    locale: str = DEFAULT_LOCALE
    tenant_id: str = Field(min_length=1)

    def as_state(self) -> AgentGraphInputState:
        return cast(AgentGraphInputState, self.model_dump(mode="python"))


class AgentState(AgentGraphInputState, total=False):
    query: str
    safe_query: str
    guard_blocked: bool
    guard_reason: str
    pii_redactions: int
    pii_details: list[PiiDetailState]
    needs_retrieval: bool
    search_query: str
    rewrite_reason: str
    indexed_document_count: int
    retrieved_chunks: list[dict[str, Any]]
    search_meta: dict[str, Any]
    answer: str
    citations: list[dict[str, Any]]


class AgentStateUpdate(TypedDict, total=False):
    query: str
    safe_query: str
    guard_blocked: bool
    guard_reason: str
    pii_redactions: int
    pii_details: list[PiiDetailState]
    needs_retrieval: bool
    search_query: str
    rewrite_reason: str
    indexed_document_count: int
    retrieved_chunks: list[dict[str, Any]]
    search_meta: dict[str, Any]
    answer: str
    citations: list[dict[str, Any]]


ChatCompiledGraph = CompiledStateGraph[
    AgentState,
    None,
    AgentGraphInputState,
    AgentState,
]


class GraphConfigurable(TypedDict, total=False):
    thread_id: str
    checkpoint_id: str


def graph_config(*, thread_id: str, checkpoint_id: str | None = None) -> RunnableConfig:
    configurable: dict[str, Any] = {"thread_id": thread_id}
    if checkpoint_id:
        configurable["checkpoint_id"] = checkpoint_id
    return {"configurable": configurable}


def locale_of(state: AgentState) -> str:
    return state.get("locale") or DEFAULT_LOCALE


def graph_messages_from_state(state: AgentState) -> list[GraphMessage]:
    return [GraphMessage.model_validate(message) for message in state.get("messages", [])]


def latest_user_content(messages: list[GraphMessage]) -> str:
    for message in reversed(messages):
        if message.role is ChatMessageRole.USER:
            return message.content
    return ""


def search_meta_from_output(output: AgentStateUpdate) -> SearchMeta | None:
    raw = output.get("search_meta")
    if not isinstance(raw, dict):
        return None
    return SearchMeta.model_validate(raw)


def citations_from_output(output: AgentStateUpdate) -> list[ChunkCitation]:
    raw = output.get("citations")
    if not isinstance(raw, list):
        return []
    out: list[ChunkCitation] = []
    for item in raw:
        if isinstance(item, dict):
            out.append(ChunkCitation.model_validate(item))
    return out
