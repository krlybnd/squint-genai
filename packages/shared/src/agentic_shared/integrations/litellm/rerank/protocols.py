from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from agentic_shared.integrations.litellm.rerank.models import RerankHit


@runtime_checkable
class RerankPort(Protocol):
    @property
    def enabled(self) -> bool: ...

    @property
    def model(self) -> str: ...

    async def rerank(
        self,
        query: str,
        documents: Sequence[str],
        *,
        top_n: int,
    ) -> list[RerankHit]: ...
