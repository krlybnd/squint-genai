from langgraph.graph import StateGraph

from agentic_chat.core.deps import AgentGraphDeps
from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.graph.workflow import GUARD_BRANCHES, LINEAR_EDGES, route_after_guard
from agentic_chat.core.nodes.protocols import GraphNode


def build_graph_nodes(deps: AgentGraphDeps) -> dict[AgentGraphNode, GraphNode]:
    from agentic_chat.core.guard.node import GuardNode
    from agentic_chat.core.nodes.block import BlockNode
    from agentic_chat.core.nodes.generate import GenerateNode
    from agentic_chat.core.nodes.plan import PlanNode
    from agentic_chat.core.nodes.retrieve import RetrieveNode
    from agentic_chat.core.nodes.rewrite.node import RewriteQueryNode

    nodes: list[GraphNode] = [
        PlanNode(),
        GuardNode(deps),
        BlockNode(),
        RewriteQueryNode(deps),
        RetrieveNode(deps),
        GenerateNode(deps),
    ]
    return {node.node_id: node for node in nodes}


def register_workflow_nodes(graph: StateGraph, deps: AgentGraphDeps) -> None:
    for node_id, handler in build_graph_nodes(deps).items():
        graph.add_node(node_id, handler)

    for source, target in LINEAR_EDGES:
        graph.add_edge(source, target)

    graph.add_conditional_edges(
        AgentGraphNode.GUARD,
        route_after_guard,
        GUARD_BRANCHES,
    )
