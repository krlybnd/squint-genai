from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from agentic_shared.integrations.llm.content import extract_chat_completion_content

from agentic_chat.core.deps import AgentGraphDeps
from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.state import AgentState, AgentStateUpdate

logger = logging.getLogger(__name__)


@runtime_checkable
class GraphNode(Protocol):
    """One LangGraph step: read shared state, return a partial update."""

    @property
    def node_id(self) -> AgentGraphNode: ...

    async def __call__(self, state: AgentState) -> AgentStateUpdate: ...


class LlmCallNode(ABC, GraphNode):
    """Template for nodes that call the chat LLM (prepare → messages → map result)."""

    def __init__(self, deps: AgentGraphDeps) -> None:
        self._deps = deps

    @property
    @abstractmethod
    def node_id(self) -> AgentGraphNode: ...

    async def prepare(self, state: AgentState) -> AgentStateUpdate | None:
        """Return an update to skip the LLM call, or ``None`` to continue."""
        return None

    @abstractmethod
    async def build_messages(self, state: AgentState) -> list[dict[str, str]]: ...

    @abstractmethod
    def on_success(self, state: AgentState, content: str) -> AgentStateUpdate: ...

    @abstractmethod
    def on_error(self, state: AgentState) -> AgentStateUpdate: ...

    async def __call__(self, state: AgentState) -> AgentStateUpdate:
        early = await self.prepare(state)
        if early is not None:
            logger.debug("%s skipped llm call", self.node_id.value)
            return early
        try:
            messages = await self.build_messages(state)
            result = await self._deps.chat_client.chat_completion(
                messages,
                temperature=self.llm_temperature(),
            )
            content = extract_chat_completion_content(result)
            return self.on_success(state, content)
        except Exception:
            logger.exception("%s LLM step failed", self.node_id.value)
            return self.on_error(state)

    def llm_temperature(self) -> float:
        return 0.2


__all__ = ["GraphNode", "LlmCallNode"]
