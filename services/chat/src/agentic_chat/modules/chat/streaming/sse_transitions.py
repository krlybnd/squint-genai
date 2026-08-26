"""Next-step ACTIVE SSE events derived from graph output (UX flow, not raw LangGraph edges)."""

from agentic_shared.core.i18n import t

from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.state import AgentStateUpdate
from agentic_chat.modules.chat.enums import ReasoningStatus, ReasoningStep
from agentic_chat.modules.chat.streaming.sse_events import (
    ReasoningEventData,
    StatusEventData,
    sse_reasoning,
    sse_status,
)


def _active(step: ReasoningStep, message: str, *, chunks: int | None = None) -> list[str]:
    events = [
        sse_reasoning(
            ReasoningEventData(step=step, message=message, status=ReasoningStatus.ACTIVE),
        ),
    ]
    if chunks is not None:
        events.append(sse_status(StatusEventData(step=step, chunks=chunks)))
    else:
        events.append(sse_status(StatusEventData(step=step)))
    return events


def active_events_after(
    node: AgentGraphNode,
    output: AgentStateUpdate,
    locale: str,
) -> list[str]:
    if node == AgentGraphNode.PLAN:
        return _active(ReasoningStep.GUARD, t("reasoning.guard_active", locale))

    if node == AgentGraphNode.GUARD:
        if output.get("guard_blocked"):
            return _active(
                ReasoningStep.GENERATE,
                t("reasoning.generate_blocked", locale),
                chunks=0,
            )
        return _active(ReasoningStep.REWRITE, t("reasoning.rewrite_active", locale))

    if node == AgentGraphNode.REWRITE:
        if output.get("needs_retrieval", True):
            return _active(ReasoningStep.RETRIEVE, t("reasoning.retrieve_active", locale))
        return _active(
            ReasoningStep.GENERATE,
            t("reasoning.generate_active", locale),
            chunks=0,
        )

    if node == AgentGraphNode.RETRIEVE:
        chunks = output.get("retrieved_chunks", [])
        count = len(chunks) if isinstance(chunks, list) else 0
        return _active(
            ReasoningStep.GENERATE,
            t("reasoning.generate_active", locale),
            chunks=count,
        )

    return []
