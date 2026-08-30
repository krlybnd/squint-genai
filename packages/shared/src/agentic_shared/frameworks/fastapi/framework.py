"""Fluent FastAPI application builder (composition — does not subclass FastAPI)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any, Self

from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentic_shared.core.banner import print_startup_banner
from agentic_shared.core.logging import setup_logging
from agentic_shared.core.package import PackageInfo
from agentic_shared.frameworks.fastapi.handlers.error_handler.handler import (
    register_domain_error_handlers,
)
from agentic_shared.frameworks.fastapi.middlewares.security_headers_middleware.middleware import (
    SecurityHeadersMiddleware,
)
from agentic_shared.frameworks.fastapi.settings import FastAPISettings

type Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]

logger = logging.getLogger(__name__)


def _csv_list(value: str) -> list[str]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    return parts if parts else ["*"]


def _cors_origins(value: str) -> list[str]:
    origins = [part.strip() for part in value.split(",") if part.strip()]
    if not origins:
        raise ValueError("CORS_ORIGINS must list at least one origin")
    if "*" in origins:
        raise ValueError(
            "CORS_ORIGINS cannot include '*'; browsers reject wildcard with credentials"
        )
    return origins


def _optional_path(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class FastAPIAppBuilder:
    """Assemble a service FastAPI app: identity, middleware, DI, routers."""

    def __init__(
        self,
        package: PackageInfo,
        *,
        settings: FastAPISettings | None = None,
        log_level: str = "INFO",
    ) -> None:
        self._package = package
        self._settings = settings or FastAPISettings()
        self._log_level = log_level
        self._lifespan: Lifespan | None = None
        self._standard_middleware = False
        self._domain_errors = False
        self._container: AsyncContainer | None = None
        self._routers: list[tuple[APIRouter, dict[str, Any]]] = []

    def lifespan(self, lifespan: Lifespan) -> Self:
        self._lifespan = lifespan
        return self

    def with_standard_middleware(self) -> Self:
        self._standard_middleware = True
        return self

    def with_domain_errors(self) -> Self:
        self._domain_errors = True
        return self

    def with_dishka(self, container: AsyncContainer) -> Self:
        self._container = container
        return self

    def include_router(self, router: APIRouter, **kwargs: Any) -> Self:
        self._routers.append((router, kwargs))
        return self

    def include_routers(self, routers: Sequence[tuple[APIRouter, dict[str, Any]]]) -> Self:
        for router, kwargs in routers:
            self._routers.append((router, kwargs))
        return self

    def build(self) -> FastAPI:
        app = FastAPI(
            title=self._package.name,
            version=self._package.version,
            description=self._package.description,
            docs_url=_optional_path(self._settings.docs_url),
            redoc_url=_optional_path(self._settings.redoc_url),
            openapi_url=_optional_path(self._settings.openapi_url),
            lifespan=self._wrapped_lifespan(),
        )
        if self._standard_middleware:
            self._apply_standard_middleware(app)
        if self._domain_errors:
            register_domain_error_handlers(app)
        if self._container is not None:
            setup_dishka(self._container, app)
        for router, kwargs in self._routers:
            app.include_router(router, **kwargs)
        return app

    def _wrapped_lifespan(self) -> Lifespan:
        package = self._package
        inner = self._lifespan
        log_level = self._log_level

        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncIterator[None]:
            setup_logging(log_level)
            print_startup_banner(package)
            logger.info("application startup")
            if inner is None:
                yield
                logger.info("application shutdown")
                return
            async with inner(app):
                yield
            logger.info("application shutdown")

        return lifespan

    def _apply_standard_middleware(self, app: FastAPI) -> None:
        settings = self._settings
        app.add_middleware(
            CORSMiddleware,
            allow_origins=_cors_origins(settings.cors_origins),
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=_csv_list(settings.cors_allow_methods),
            allow_headers=_csv_list(settings.cors_allow_headers),
        )
        if settings.security_headers.enabled:
            app.add_middleware(
                SecurityHeadersMiddleware,
                headers=settings.security_headers.as_headers(),
            )
