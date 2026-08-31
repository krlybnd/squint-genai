import logging

from agentic_shared.crosscut.i18n import t
from agentic_shared.domains.pii_vault.protocols import QueryPiiTokenizationPort
from agentic_shared.integrations.litellm.analyzer.protocols import Analyzer
from agentic_shared.integrations.litellm.anonymizer.protocols import Anonymizer
from agentic_shared.integrations.litellm.guard.errors import GuardError
from agentic_shared.integrations.litellm.guard.protocols import Guard

from agentic_chat.core.guard.pii import mask_text
from agentic_chat.core.guard.protocols import GuardRule
from agentic_chat.core.state import AgentStateUpdate
from agentic_chat.core.state.updates import (
    guard_empty_query_update,
    guard_injection_update,
    guard_redacted_update,
)

logger = logging.getLogger(__name__)

__all__ = [
    "EmptyQueryRule",
    "PiiRedactionRule",
    "PromptInjectionRule",
    "VaultPiiRedactionRule",
]


class EmptyQueryRule(GuardRule):
    async def evaluate(
        self,
        query: str,
        locale: str,
        *,
        tenant_id: str,
    ) -> AgentStateUpdate | None:
        if not query:
            return guard_empty_query_update(reason=t("guard.empty_query", locale))
        return None


class PromptInjectionRule(GuardRule):
    def __init__(self, guard: Guard) -> None:
        self._guard = guard

    async def evaluate(
        self,
        query: str,
        locale: str,
        *,
        tenant_id: str,
    ) -> AgentStateUpdate | None:
        try:
            result = await self._guard.analyze_prompt(query)
        except GuardError:
            logger.warning("prompt injection scan unavailable; continuing", exc_info=True)
            return None
        if result.is_injection:
            logger.warning("prompt injection detected")
            return guard_injection_update(
                reason=t("guard.injection", locale),
                answer=t("guard.injection_answer", locale),
            )
        return None


class PiiRedactionRule(GuardRule):
    """Terminal rule: always applies masking (never returns ``None``)."""

    def __init__(self, analyzer: Analyzer, anonymizer: Anonymizer) -> None:
        self._analyzer = analyzer
        self._anonymizer = anonymizer

    async def evaluate(
        self,
        query: str,
        locale: str,
        *,
        tenant_id: str,
    ) -> AgentStateUpdate | None:
        masked = await mask_text(
            query,
            analyzer=self._analyzer,
            anonymizer=self._anonymizer,
        )
        if masked.count:
            logger.debug("pii masked count=%d", masked.count)
            reason = t("guard.pii_masked", locale, count=masked.count)
        else:
            reason = t("guard.ok", locale)
        return guard_redacted_update(
            safe_query=masked.text,
            pii_redactions=masked.count,
            pii_details=masked.details,
            reason=reason,
        )


class VaultPiiRedactionRule(GuardRule):
    """Terminal rule: vault deterministic tokens (matches index-time tokenizer)."""

    def __init__(self, query_pii: QueryPiiTokenizationPort) -> None:
        self._query_pii = query_pii

    async def evaluate(
        self,
        query: str,
        locale: str,
        *,
        tenant_id: str,
    ) -> AgentStateUpdate | None:
        tokenized = await self._query_pii.tokenize_query(query, tenant_id=tenant_id)
        changed = tokenized != query.strip()
        if changed:
            logger.debug("vault query tokenized tenant_id=%s", tenant_id)
            reason = t("guard.pii_masked", locale, count=1)
        else:
            reason = t("guard.ok", locale)
        return guard_redacted_update(
            safe_query=tokenized,
            pii_redactions=1 if changed else 0,
            pii_details=[],
            reason=reason,
        )
