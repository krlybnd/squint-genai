import logging

from agentic_shared.core.i18n import t

from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.nodes.protocols import GraphNode
from agentic_chat.core.state import AgentState, AgentStateUpdate, block_update, locale_of

logger = logging.getLogger(__name__)


class BlockNode(GraphNode):
    @property
    def node_id(self) -> AgentGraphNode:
        return AgentGraphNode.BLOCK

    async def __call__(self, state: AgentState) -> AgentStateUpdate:
        locale = locale_of(state)
        logger.info("blocked query")
        return block_update(answer=state.get("answer") or t("guard.blocked_default", locale))
