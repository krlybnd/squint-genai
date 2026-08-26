from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingClient(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
