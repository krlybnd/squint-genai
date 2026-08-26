"""LangGraph workflow: plan → guard → rewrite → retrieve → generate."""

from typing import cast

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph

from agentic_chat.core.deps import AgentGraphDeps, agent_graph_deps_from_settings
from agentic_chat.core.graph.registry import register_workflow_nodes
from agentic_chat.core.state import AgentState, ChatCompiledGraph


def build_graph(
    checkpointer: BaseCheckpointSaver,
    *,
    deps: AgentGraphDeps | None = None,
) -> ChatCompiledGraph:
    resolved_deps = deps or agent_graph_deps_from_settings()
    graph = StateGraph(AgentState)
    register_workflow_nodes(graph, resolved_deps)
    return cast(ChatCompiledGraph, graph.compile(checkpointer=checkpointer))
