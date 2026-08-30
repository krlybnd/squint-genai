import logging

from agentic_chat.core.deps import AgentGraphDeps
from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.guard.protocols import GuardRule, default_guard_rules
from agentic_chat.core.nodes.protocols import GraphNode
from agentic_chat.core.state import AgentState, AgentStateUpdate, locale_of

logger = logging.getLogger(__name__)


class GuardNode(GraphNode):
    def __init__(
        self,
        deps: AgentGraphDeps | None = None,
        *,
        rules: tuple[GuardRule, ...] | None = None,
    ) -> None:
        if rules is not None:
            self._rules = rules
        elif deps is not None:
            self._rules = default_guard_rules(
                deps.guard,
                deps.analyzer,
                deps.anonymizer,
                query_pii=deps.query_pii,
            )
        else:
            raise TypeError("GuardNode requires deps or rules")

    @property
    def node_id(self) -> AgentGraphNode:
        return AgentGraphNode.GUARD

    async def __call__(self, state: AgentState) -> AgentStateUpdate:
        query = (state.get("query") or "").strip()
        locale = locale_of(state)
        tenant_id = state.get("tenant_id") or "default"
        for rule in self._rules:
            result = await rule.evaluate(query, locale, tenant_id=tenant_id)
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
