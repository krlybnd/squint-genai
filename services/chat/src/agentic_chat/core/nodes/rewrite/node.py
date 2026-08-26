import json
import logging
import re

from agentic_shared.core.i18n import t
from agentic_shared.domains.retrieval.models import IndexedDocumentEntry
from agentic_shared.integrations.llm.messages import llm_system_user

from agentic_chat.core.deps import AgentGraphDeps
from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.nodes.protocols import LlmCallNode
from agentic_chat.core.nodes.rewrite.models import RewriteRouterResponse
from agentic_chat.core.nodes.rewrite.prompt import build_rewrite_router_system_prompt
from agentic_chat.core.nodes.rewrite.settings import get_module_settings
from agentic_chat.core.state import AgentState, AgentStateUpdate, locale_of
from agentic_chat.core.state.updates import rewrite_routing_update

_JSON_BLOCK = re.compile(r"\{[\s\S]*\}")

logger = logging.getLogger(__name__)


def _parse_rewrite_response(content: str) -> RewriteRouterResponse:
    raw = content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0].strip()
    match = _JSON_BLOCK.search(raw)
    if not match:
        raise ValueError("No JSON object in LLM response")
    parsed = json.loads(match.group())
    if not isinstance(parsed, dict):
        raise ValueError("LLM JSON is not an object")
    return RewriteRouterResponse.model_validate(parsed)


class RewriteQueryNode(LlmCallNode):
    def __init__(self, deps: AgentGraphDeps) -> None:
        super().__init__(deps)
        self._locale = ""
        self._query = ""
        self._indexed: list[IndexedDocumentEntry] = []

    @property
    def node_id(self) -> AgentGraphNode:
        return AgentGraphNode.REWRITE

    async def prepare(self, state: AgentState) -> AgentStateUpdate | None:
        self._locale = locale_of(state)
        self._query = state.get("safe_query") or state.get("query", "")
        tenant_id = state.get("tenant_id") or "default"
        self._indexed = await self._deps.retrieval.list_indexed_documents(tenant_id=tenant_id)
        return None

    async def build_messages(self, state: AgentState) -> list[dict[str, str]]:
        system = build_rewrite_router_system_prompt(indexed=self._indexed)
        return llm_system_user(system, self._query)

    def on_success(self, state: AgentState, content: str) -> AgentStateUpdate:
        parsed = _parse_rewrite_response(content)
        needs = parsed.needs_document_search
        search_query = parsed.search_query.strip()
        reason = parsed.rewrite_reason.strip()
        if needs and not search_query:
            search_query = self._query
        logger.debug(
            "rewrite routing needs_retrieval=%s indexed=%d",
            needs,
            len(self._indexed),
        )
        return rewrite_routing_update(
            needs_retrieval=needs,
            search_query=search_query if needs else "",
            rewrite_reason=reason
            or (
                t("rewrite.search_needed", self._locale)
                if needs
                else t("rewrite.no_search", self._locale)
            ),
            indexed_document_count=len(self._indexed),
        )

    def on_error(self, state: AgentState) -> AgentStateUpdate:
        logger.warning("rewrite fallback to retrieval indexed=%d", len(self._indexed))
        return rewrite_routing_update(
            needs_retrieval=True,
            search_query=self._query,
            rewrite_reason=t("rewrite.fallback", self._locale),
            indexed_document_count=len(self._indexed),
        )

    def llm_temperature(self) -> float:
        return get_module_settings().llm_temperature
