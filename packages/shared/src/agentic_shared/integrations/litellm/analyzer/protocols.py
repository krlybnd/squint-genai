from typing import Protocol, runtime_checkable

from agentic_shared.integrations.litellm.analyzer.models import AnalyzerEntity


@runtime_checkable
class Analyzer(Protocol):
    async def analyze(self, text: str, *, language: str = "en") -> list[AnalyzerEntity]: ...
