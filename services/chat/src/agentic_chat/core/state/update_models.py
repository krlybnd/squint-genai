from __future__ import annotations

from typing import Any, Self, cast

from agentic_shared.domains.retrieval.models import ChunkCitation, SearchMeta
from pydantic import BaseModel, ConfigDict, Field

from agentic_chat.core.state.models import citation_states, search_meta_state
from agentic_chat.core.state.schema import AgentStateUpdate, PiiDetailState


class StateUpdateModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    def to_update(self) -> AgentStateUpdate:
        return cast(AgentStateUpdate, self.model_dump(mode="python"))


class PlanUpdate(StateUpdateModel):
    query: str


class GuardEmptyQueryUpdate(StateUpdateModel):
    safe_query: str = ""
    guard_blocked: bool = False
    pii_redactions: int = 0
    guard_reason: str


class GuardInjectionUpdate(StateUpdateModel):
    safe_query: str = ""
    guard_blocked: bool = True
    pii_redactions: int = 0
    guard_reason: str
    answer: str
    needs_retrieval: bool = False
    search_query: str = ""
    citations: list[dict[str, Any]] = Field(default_factory=list)


class GuardRedactedUpdate(StateUpdateModel):
    safe_query: str
    pii_redactions: int
    pii_details: list[PiiDetailState]
    guard_blocked: bool = False
    guard_reason: str


class BlockUpdate(StateUpdateModel):
    answer: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    needs_retrieval: bool = False


class RewriteRoutingUpdate(StateUpdateModel):
    needs_retrieval: bool
    search_query: str
    rewrite_reason: str
    indexed_document_count: int


class RetrieveResultUpdate(StateUpdateModel):
    retrieved_chunks: list[dict[str, Any]]
    search_meta: dict[str, Any]

    @classmethod
    def from_search(
        cls,
        *,
        retrieved_chunks: list[dict[str, Any]],
        search_meta: SearchMeta,
    ) -> Self:
        return cls(
            retrieved_chunks=retrieved_chunks,
            search_meta=search_meta_state(search_meta),
        )


class GenerateAnswerUpdate(StateUpdateModel):
    answer: str
    citations: list[dict[str, Any]]

    @classmethod
    def from_citations(
        cls,
        *,
        answer: str,
        citations: list[ChunkCitation],
    ) -> Self:
        return cls(answer=answer, citations=citation_states(citations))
