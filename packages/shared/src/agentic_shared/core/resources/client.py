from __future__ import annotations

import logging
from types import TracebackType
from typing import Self

from agentic_shared.core.resources.settings import ResourceSettings


class BaseResourceClient[S: ResourceSettings]:
    def __init__(self, settings: S) -> None:
        self._settings = settings
        self._logger = logging.getLogger(self.__class__.__module__)
        self._closed = False

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
        self._logger.info("closed %s", self.title)

    async def __aenter__(self) -> Self:
        self._logger.info("opened %s", self.title)
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
