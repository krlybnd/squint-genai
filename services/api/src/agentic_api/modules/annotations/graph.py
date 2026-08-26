from collections.abc import Awaitable, Callable
from typing import Protocol, cast

from langgraph.graph import END, START, StateGraph

from agentic_api.modules.annotations.deps import CommentGraphDeps
from agentic_api.modules.annotations.enums import CommentGraphNode
from agentic_api.modules.annotations.nodes import moderate_node, persist_node, reject_node
from agentic_api.modules.annotations.state import (
    CommentCompiledGraph,
    CommentState,
    CommentStateUpdate,
)


class _AddGraphNode(Protocol):
    """LangGraph's add_node overloads do not accept TypedDict partial updates."""

    def __call__(
        self,
        node: CommentGraphNode,
        action: Callable[[CommentState], Awaitable[CommentState]]
        | Callable[[CommentState], CommentState],
    ) -> object: ...


def _bind(
    fn: Callable[..., Awaitable[CommentStateUpdate]],
    deps: CommentGraphDeps,
) -> Callable[[CommentState], Awaitable[CommentState]]:
    async def wrapped(state: CommentState) -> CommentState:
        return cast(CommentState, await fn(state, deps))

    return wrapped


def _reject(state: CommentState) -> CommentState:
    return cast(CommentState, reject_node(state))


def _route_after_moderate(state: CommentState) -> CommentGraphNode:
    return CommentGraphNode.PERSIST if state.get("approved") else CommentGraphNode.REJECT


def build_comment_graph(deps: CommentGraphDeps) -> CommentCompiledGraph:
    graph = StateGraph(CommentState)
    add_node = cast(_AddGraphNode, graph.add_node)
    add_node(CommentGraphNode.MODERATE, _bind(moderate_node, deps))
    add_node(CommentGraphNode.PERSIST, _bind(persist_node, deps))
    add_node(CommentGraphNode.REJECT, _reject)
    graph.add_edge(START, CommentGraphNode.MODERATE)
    graph.add_conditional_edges(
        CommentGraphNode.MODERATE,
        _route_after_moderate,
        {
            CommentGraphNode.PERSIST: CommentGraphNode.PERSIST,
            CommentGraphNode.REJECT: CommentGraphNode.REJECT,
        },
    )
    graph.add_edge(CommentGraphNode.PERSIST, END)
    graph.add_edge(CommentGraphNode.REJECT, END)
    return cast(CommentCompiledGraph, graph.compile())
