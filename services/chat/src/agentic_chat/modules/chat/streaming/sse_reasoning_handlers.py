"""Node-specific SSE 'done' reasoning payloads (no transition / next-step logic)."""

from collections.abc import Callable

from agentic_shared.core.i18n import t

from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.state import AgentStateUpdate, PiiDetailState
from agentic_chat.modules.chat.enums import ReasoningStatus, ReasoningStep
from agentic_chat.modules.chat.streaming.sse_events import ReasoningEventData

NodeDoneHandler = Callable[[AgentStateUpdate, str], ReasoningEventData]


def _plan_done(output: AgentStateUpdate, locale: str) -> ReasoningEventData:
    query = output.get("query", "")
    return ReasoningEventData(
        step=ReasoningStep.PLAN,
        message=t("reasoning.plan", locale, query=query)
        if query
        else t("reasoning.plan_pending", locale),
        status=ReasoningStatus.DONE,
    )


def _guard_done(output: AgentStateUpdate, locale: str) -> ReasoningEventData:
    reason = output.get("guard_reason", "")
    redactions = output.get("pii_redactions", 0)
    blocked = output.get("guard_blocked", False)
    if blocked:
        msg = reason or t("reasoning.guard_rejected", locale)
    elif redactions:
        msg = f"{reason or t('reasoning.guard_pii_fallback', locale)} ({redactions})"
    else:
        msg = reason or t("guard.ok", locale)
    pii_details = output.get("pii_details", [])
    details: list[PiiDetailState] | None = None
    if isinstance(pii_details, list) and pii_details:
        details = [d for d in pii_details if isinstance(d, dict)]
    return ReasoningEventData(
        step=ReasoningStep.GUARD,
        message=msg,
        status=ReasoningStatus.DONE,
        pii_redactions=redactions or None,
        pii_details=details,
        safe_query=output.get("safe_query") or None,
    )


def _rewrite_done(output: AgentStateUpdate, locale: str) -> ReasoningEventData:
    needs = output.get("needs_retrieval", True)
    reason = output.get("rewrite_reason", "")
    search_q = output.get("search_query", "")
    indexed_count = output.get("indexed_document_count", 0)
    if needs and search_q:
        msg = t("reasoning.search_query", locale, query=search_q)
        if reason:
            msg = f"{msg} — {reason}"
    elif needs:
        msg = reason or t("rewrite.search_needed", locale)
    else:
        msg = reason or t("rewrite.no_search", locale)
    return ReasoningEventData(
        step=ReasoningStep.REWRITE,
        message=msg,
        status=ReasoningStatus.DONE,
        needs_retrieval=needs,
        search_query=search_q or None,
        rewrite_reason=reason or None,
        indexed_document_count=indexed_count or None,
    )


def _retrieve_done(output: AgentStateUpdate, locale: str) -> ReasoningEventData:
    chunks = output.get("retrieved_chunks", [])
    count = len(chunks) if isinstance(chunks, list) else 0
    search_meta = output.get("search_meta")
    meta = search_meta if isinstance(search_meta, dict) else None
    return ReasoningEventData(
        step=ReasoningStep.RETRIEVE,
        message=t("reasoning.retrieve_done", locale, count=count),
        status=ReasoningStatus.DONE,
        chunks=count,
        search_meta=meta,
    )


def _generate_done(_output: AgentStateUpdate, locale: str) -> ReasoningEventData:
    return ReasoningEventData(
        step=ReasoningStep.GENERATE,
        message=t("reasoning.generate_done", locale),
        status=ReasoningStatus.DONE,
    )


NODE_DONE_HANDLERS: dict[AgentGraphNode, NodeDoneHandler] = {
    AgentGraphNode.PLAN: _plan_done,
    AgentGraphNode.GUARD: _guard_done,
    AgentGraphNode.REWRITE: _rewrite_done,
    AgentGraphNode.RETRIEVE: _retrieve_done,
    AgentGraphNode.GENERATE: _generate_done,
    AgentGraphNode.BLOCK: _generate_done,
}
