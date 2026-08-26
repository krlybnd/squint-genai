from typing import Protocol, runtime_checkable

from agentic_chat.core.state import AgentStateUpdate


@runtime_checkable
class GuardRule(Protocol):
    """Returns a state update when the rule applies, or ``None`` to defer."""

    def evaluate(self, query: str, locale: str) -> AgentStateUpdate | None: ...


def default_guard_rules() -> tuple[GuardRule, ...]:
    from agentic_chat.core.guard.rules import (
        EmptyQueryRule,
        PiiRedactionRule,
        PromptInjectionRule,
    )

    return (
        EmptyQueryRule(),
        PromptInjectionRule(),
        PiiRedactionRule(),
    )


DEFAULT_GUARD_RULES: tuple[GuardRule, ...] = default_guard_rules()

__all__ = [
    "DEFAULT_GUARD_RULES",
    "GuardRule",
    "default_guard_rules",
]
