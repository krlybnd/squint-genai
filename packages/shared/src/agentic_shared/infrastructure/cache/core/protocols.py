from typing import Protocol, runtime_checkable


@runtime_checkable
class CacheReader(Protocol):
    def ping(self) -> bool: ...

    def get(self, key: str) -> bytes | None: ...


@runtime_checkable
class CacheWriter(Protocol):
    def set(self, key: str, value: bytes | str, *, ex: int | None = None) -> None: ...

    def delete(self, key: str) -> None: ...
