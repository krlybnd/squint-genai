import json
import logging
import re
from dataclasses import dataclass

from agentic_shared.crosscut.i18n import t
from agentic_shared.domains.retrieval.models import IndexedDocumentEntry
from agentic_shared.integrations.litellm.llm.messages import llm_system_user
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings

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


@dataclass(frozen=True)
class _RewriteContext:
    locale: str
    query: str
    indexed: list[IndexedDocumentEntry]


class RewriteQueryNode(LlmCallNode[_RewriteContext]):
    def __init__(self, deps: AgentGraphDeps) -> None:
        super().__init__(deps)

    @property
    def node_id(self) -> AgentGraphNode:
        return AgentGraphNode.REWRITE

    async def prepare(self, state: AgentState) -> tuple[AgentStateUpdate | None, _RewriteContext]:
        locale = locale_of(state)
        query = state.get("safe_query") or state.get("query", "")
        tenant_id = state.get("tenant_id") or "default"
        indexed = await self._deps.retrieval.list_indexed_documents(tenant_id=tenant_id)
        return None, _RewriteContext(locale=locale, query=query, indexed=indexed)

    async def build_messages(self, state: AgentState, ctx: _RewriteContext) -> list[dict[str, str]]:
        system = build_rewrite_router_system_prompt(indexed=ctx.indexed)
        return llm_system_user(system, ctx.query)

    def on_success(self, state: AgentState, content: str, ctx: _RewriteContext) -> AgentStateUpdate:
        parsed = _parse_rewrite_response(content)
        needs = parsed.needs_document_search
        # Keep the original utterance (Elasticsearch / LangChain include_original):
        # LLM query rewrites drop rare terms and can change language.
        original = (state.get("query") or ctx.query).strip()
        search_query = original if needs else ""
        reason = parsed.rewrite_reason.strip()
        logger.debug(
            "rewrite routing needs_retrieval=%s indexed=%d",
            needs,
            len(ctx.indexed),
        )
        return rewrite_routing_update(
            needs_retrieval=needs,
            search_query=search_query if needs else "",
            rewrite_reason=reason
            or (
                t("rewrite.search_needed", ctx.locale)
                if needs
                else t("rewrite.no_search", ctx.locale)
            ),
            indexed_document_count=len(ctx.indexed),
        )

    def on_error(self, state: AgentState, ctx: _RewriteContext) -> AgentStateUpdate:
        logger.warning("rewrite fallback to retrieval indexed=%d", len(ctx.indexed))
        return rewrite_routing_update(
            needs_retrieval=True,
            search_query=ctx.query,
            rewrite_reason=t("rewrite.fallback", ctx.locale),
            indexed_document_count=len(ctx.indexed),
        )

    def llm_temperature(self) -> float:
        return get_module_settings().llm_temperature

    def llm_model(self) -> str | None:
        return LiteLLMChatSettings().litellm_router_model
