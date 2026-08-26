import logging
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentic_shared.core.banner import print_startup_banner
from agentic_shared.core.logging import setup_logging
from agentic_shared.frameworks.fastapi.auth.middleware import SecurityHeadersMiddleware
from agentic_shared.frameworks.fastapi.cors import CorsSettings

type _Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]

logger = logging.getLogger(__name__)


def apply_standard_http_middleware(
    app: FastAPI,
    *,
    cors: CorsSettings | None = None,
) -> None:
    settings = cors or CorsSettings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origin_list(),
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)


def _with_startup_banner(
    service: str,
    version: str,
    inner: _Lifespan | None,
    log_level: str,
) -> _Lifespan:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        setup_logging(log_level)
        print_startup_banner(service, version)
        logger.info("application startup")
        if inner is None:
            yield
            logger.info("application shutdown")
            return
        async with inner(app):
            yield
        logger.info("application shutdown")

    return lifespan


def create_fastapi_service_app(
    *,
    title: str,
    description: str,
    version: str = "0.1.0",
    log_level: str = "INFO",
    lifespan: _Lifespan | None = None,
) -> FastAPI:
    return FastAPI(
        title=title,
        version=version,
        description=description,
        lifespan=_with_startup_banner(title, version, lifespan, log_level),
    )
