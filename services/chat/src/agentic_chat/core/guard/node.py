import logging

from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.guard.protocols import DEFAULT_GUARD_RULES, GuardRule
from agentic_chat.core.nodes.protocols import GraphNode
from agentic_chat.core.state import AgentState, AgentStateUpdate, locale_of

logger = logging.getLogger(__name__)


class GuardNode(GraphNode):
    def __init__(self, rules: tuple[GuardRule, ...] = DEFAULT_GUARD_RULES) -> None:
        self._rules = rules

    @property
    def node_id(self) -> AgentGraphNode:
        return AgentGraphNode.GUARD

    async def __call__(self, state: AgentState) -> AgentStateUpdate:
        query = (state.get("query") or "").strip()
        locale = locale_of(state)
        for rule in self._rules:
            result = rule.evaluate(query, locale)
            if result is not None:
                if result.get("guard_blocked"):
                    logger.warning("guard blocked rule=%s", rule.__class__.__name__)
                else:
                    logger.debug(
                        "guard passed rule=%s pii=%s",
                        rule.__class__.__name__,
                        result.get("pii_redactions", 0),
                    )
                return result
        raise RuntimeError("guard rule chain produced no update")
