import logging

from agentic_shared.core.security.guard import looks_like_prompt_injection, redact_pii
from agentic_shared.crosscut.i18n import t

from agentic_chat.core.guard.protocols import GuardRule
from agentic_chat.core.state import AgentStateUpdate, PiiDetail, PiiDetailState
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
]


class EmptyQueryRule(GuardRule):
    def evaluate(self, query: str, locale: str) -> AgentStateUpdate | None:
        if not query:
            return guard_empty_query_update(reason=t("guard.empty_query", locale))
        return None


class PromptInjectionRule(GuardRule):
    def evaluate(self, query: str, locale: str) -> AgentStateUpdate | None:
        if looks_like_prompt_injection(query):
            logger.warning("prompt injection detected")
            return guard_injection_update(
                reason=t("guard.injection", locale),
                answer=t("guard.injection_answer", locale),
            )
        return None


class PiiRedactionRule(GuardRule):
    """Terminal rule: always applies redaction (never returns ``None``)."""

    def evaluate(self, query: str, locale: str) -> AgentStateUpdate | None:
        redacted = redact_pii(query)
        if redacted.count:
            logger.debug("pii redacted count=%d", redacted.count)
            reason = t("guard.pii_masked", locale, count=redacted.count)
        else:
            reason = t("guard.ok", locale)
        pii_details: list[PiiDetailState] = [
            PiiDetail(kind=d.kind, placeholder=d.placeholder).as_state() for d in redacted.details
        ]
        return guard_redacted_update(
            safe_query=redacted.text,
            pii_redactions=redacted.count,
            pii_details=pii_details,
            reason=reason,
        )
