from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class ResourceClient(Protocol):
    @property
    def title(self) -> str: ...

    async def health_check(self) -> bool: ...

    async def aclose(self) -> None: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
