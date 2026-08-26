from typing import Protocol, runtime_checkable


@runtime_checkable
class ResourceHealthCheckable(Protocol):
    @property
    def title(self) -> str: ...

    async def health_check(self) -> bool: ...
