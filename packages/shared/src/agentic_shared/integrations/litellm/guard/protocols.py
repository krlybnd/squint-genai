from typing import Protocol, runtime_checkable

from agentic_shared.integrations.litellm.guard.models import GuardResult


@runtime_checkable
class Guard(Protocol):
    async def analyze_prompt(self, prompt: str) -> GuardResult: ...
