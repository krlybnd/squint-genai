from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import TracebackType
from typing import Protocol, Self, TypeVar, runtime_checkable

from agentic_shared.core.resources.settings import ResourceSettings

T = TypeVar("T", bound="ResourceClient")


@runtime_checkable
class ResourceClient(Protocol):
    @property
    def title(self) -> str: ...

    async def health_check(self) -> bool: ...

    async def aclose(self) -> None: ...


class BaseResourceClient[S: ResourceSettings]:
    def __init__(self, settings: S) -> None:
        self._settings = settings
        self._logger = logging.getLogger(self.__class__.__module__)
        self._closed = False
        self._logger.info("opening %s", self.title)

    @property
    def title(self) -> str:
        return self._settings.title

    async def health_check(self) -> bool:
        raise NotImplementedError

    async def aclose(self) -> None:
        self.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._logger.info("closing %s", self.title)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        _tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self._logger.error("exit %s with error", self.title, exc_info=exc)
        await self.aclose()


@asynccontextmanager
async def open_resource[T: "ResourceClient"](client: T) -> AsyncIterator[T]:
    """Yield a resource client and always run teardown."""
    try:
        yield client
    finally:
        await client.aclose()
