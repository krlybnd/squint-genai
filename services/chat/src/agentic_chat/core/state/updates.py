"""Typed partial state updates returned from LangGraph nodes."""

from __future__ import annotations

from typing import Any

from agentic_shared.domains.retrieval.models import ChunkCitation, SearchMeta

from agentic_chat.core.state.schema import AgentStateUpdate, PiiDetailState
from agentic_chat.core.state.update_models import (
    BlockUpdate,
    GenerateAnswerUpdate,
    GuardEmptyQueryUpdate,
    GuardInjectionUpdate,
    GuardRedactedUpdate,
    PlanUpdate,
    RetrieveResultUpdate,
    RewriteRoutingUpdate,
)


def plan_update(*, query: str) -> AgentStateUpdate:
    return PlanUpdate(query=query).to_update()


def guard_empty_query_update(*, reason: str) -> AgentStateUpdate:
    return GuardEmptyQueryUpdate(guard_reason=reason).to_update()


def guard_injection_update(*, reason: str, answer: str) -> AgentStateUpdate:
    return GuardInjectionUpdate(guard_reason=reason, answer=answer).to_update()


def guard_redacted_update(
    *,
    safe_query: str,
    pii_redactions: int,
    pii_details: list[PiiDetailState],
    reason: str,
) -> AgentStateUpdate:
    return GuardRedactedUpdate(
        safe_query=safe_query,
        pii_redactions=pii_redactions,
        pii_details=pii_details,
        guard_reason=reason,
    ).to_update()


def block_update(*, answer: str) -> AgentStateUpdate:
    return BlockUpdate(answer=answer).to_update()


def rewrite_routing_update(
    *,
    needs_retrieval: bool,
    search_query: str,
    rewrite_reason: str,
    indexed_document_count: int,
) -> AgentStateUpdate:
    return RewriteRoutingUpdate(
        needs_retrieval=needs_retrieval,
        search_query=search_query,
        rewrite_reason=rewrite_reason,
        indexed_document_count=indexed_document_count,
    ).to_update()


def retrieve_result_update(
    *,
    retrieved_chunks: list[dict[str, Any]],
    search_meta: SearchMeta,
) -> AgentStateUpdate:
    return RetrieveResultUpdate.from_search(
        retrieved_chunks=retrieved_chunks,
        search_meta=search_meta,
    ).to_update()


def generate_answer_update(
    *,
    answer: str,
    citations: list[ChunkCitation],
) -> AgentStateUpdate:
    return GenerateAnswerUpdate.from_citations(answer=answer, citations=citations).to_update()
