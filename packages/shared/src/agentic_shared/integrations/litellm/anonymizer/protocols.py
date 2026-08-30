from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from agentic_shared.integrations.litellm.analyzer.models import AnalyzerEntity
from agentic_shared.integrations.litellm.anonymizer.models import AnonymizeResult


@runtime_checkable
class Anonymizer(Protocol):
    async def anonymize(
        self,
        text: str,
        analyzer_results: Sequence[AnalyzerEntity],
    ) -> AnonymizeResult: ...
