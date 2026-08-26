"""Extract latest user message for the plan step."""

from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.nodes.protocols import GraphNode
from agentic_chat.core.state import (
    AgentState,
    AgentStateUpdate,
    graph_messages_from_state,
    latest_user_content,
    plan_update,
)


class PlanNode(GraphNode):
    @property
    def node_id(self) -> AgentGraphNode:
        return AgentGraphNode.PLAN

    async def __call__(self, state: AgentState) -> AgentStateUpdate:
        return plan_update(query=latest_user_content(graph_messages_from_state(state)))
