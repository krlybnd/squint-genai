from typing import Protocol, runtime_checkable

from agentic_shared.integrations.litellm.analyzer.protocols import Analyzer
from agentic_shared.integrations.litellm.anonymizer.protocols import Anonymizer
from agentic_shared.integrations.litellm.guard.protocols import Guard

from agentic_chat.core.state import AgentStateUpdate


@runtime_checkable
class GuardRule(Protocol):
    """Returns a state update when the rule applies, or ``None`` to defer."""

    async def evaluate(self, query: str, locale: str) -> AgentStateUpdate | None: ...


def default_guard_rules(
    guard: Guard,
    analyzer: Analyzer,
    anonymizer: Anonymizer,
) -> tuple[GuardRule, ...]:
    from agentic_chat.core.guard.rules import (
        EmptyQueryRule,
        PiiRedactionRule,
        PromptInjectionRule,
    )

    return (
        EmptyQueryRule(),
        PromptInjectionRule(guard),
        PiiRedactionRule(analyzer, anonymizer),
    )


__all__ = [
    "GuardRule",
    "default_guard_rules",
]
