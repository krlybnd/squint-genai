from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Protocol, TypeVar, runtime_checkable

from agentic_shared.integrations.llm.content import extract_chat_completion_content

from agentic_chat.core.deps import AgentGraphDeps
from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.state import AgentState, AgentStateUpdate

logger = logging.getLogger(__name__)

TContext = TypeVar("TContext")


@runtime_checkable
class GraphNode(Protocol):
    """One LangGraph step: read shared state, return a partial update."""

    @property
    def node_id(self) -> AgentGraphNode: ...

    async def __call__(self, state: AgentState) -> AgentStateUpdate: ...


class LlmCallNode[TContext](ABC):
    """Template for nodes that call the chat LLM (prepare → messages → map result)."""

    def __init__(self, deps: AgentGraphDeps) -> None:
        self._deps = deps

    @property
    @abstractmethod
    def node_id(self) -> AgentGraphNode: ...

    @abstractmethod
    async def prepare(self, state: AgentState) -> tuple[AgentStateUpdate | None, TContext]:
        """Return an early update to skip the LLM call, or ``(None, ctx)`` to continue."""

    @abstractmethod
    async def build_messages(self, state: AgentState, ctx: TContext) -> list[dict[str, str]]: ...

    @abstractmethod
    def on_success(self, state: AgentState, content: str, ctx: TContext) -> AgentStateUpdate: ...

    @abstractmethod
    def on_error(self, state: AgentState, ctx: TContext) -> AgentStateUpdate: ...

    async def __call__(self, state: AgentState) -> AgentStateUpdate:
        early, ctx = await self.prepare(state)
        if early is not None:
            logger.debug("%s skipped llm call", self.node_id.value)
            return early
        try:
            messages = await self.build_messages(state, ctx)
            result = await self._deps.chat_client.chat_completion(
                messages,
                temperature=self.llm_temperature(),
                model=self.llm_model(),
            )
            content = extract_chat_completion_content(result)
            return self.on_success(state, content, ctx)
        except Exception:
            logger.exception("%s LLM step failed", self.node_id.value)
            return self.on_error(state, ctx)

    def llm_temperature(self) -> float:
        return 0.2

    def llm_model(self) -> str | None:
        """LiteLLM alias; ``None`` uses the chat client's default (``generate``)."""
        return None


__all__ = ["GraphNode", "LlmCallNode", "TContext"]
