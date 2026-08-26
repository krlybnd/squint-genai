"""Declarative chat agent workflow topology (LangGraph wiring reads this)."""

from collections.abc import Hashable

from langgraph.graph import END, START

from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.state import AgentState

LINEAR_EDGES: tuple[tuple[str, str], ...] = (
    (START, AgentGraphNode.PLAN),
    (AgentGraphNode.PLAN, AgentGraphNode.GUARD),
    (AgentGraphNode.BLOCK, END),
    (AgentGraphNode.REWRITE, AgentGraphNode.RETRIEVE),
    (AgentGraphNode.RETRIEVE, AgentGraphNode.GENERATE),
    (AgentGraphNode.GENERATE, END),
)

GUARD_BRANCHES: dict[Hashable, str] = {
    AgentGraphNode.BLOCK: AgentGraphNode.BLOCK,
    AgentGraphNode.REWRITE: AgentGraphNode.REWRITE,
}


def route_after_guard(state: AgentState) -> AgentGraphNode:
    return AgentGraphNode.BLOCK if state.get("guard_blocked") else AgentGraphNode.REWRITE
