from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from agentic_shared.core.auth.providers import AuthProvider
from agentic_shared.core.ioc import infrastructure_health_provider
from agentic_shared.core.ioc.container import make_service_container
from agentic_shared.domains.persistence.providers import AsyncDbProvider
from agentic_shared.frameworks.fastapi.bootstrap import (
    apply_standard_http_middleware,
    create_fastapi_service_app,
)
from agentic_shared.frameworks.fastapi.domain_errors import register_domain_error_handlers
from agentic_shared.frameworks.fastapi.health import router as health_router
from agentic_shared.infrastructure.object_storage.providers import StorageProvider
from agentic_shared.infrastructure.postgres.providers import DatabaseProvider
from agentic_shared.infrastructure.redis.providers import RedisProvider
from agentic_shared.infrastructure.vector.providers import QdrantProvider
from agentic_shared.integrations.embedding.providers import EmbeddingProvider
from agentic_shared.integrations.llm.providers import LLMProvider
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from agentic_api.modules.annotations.providers import AnnotationsProvider
from agentic_api.modules.annotations.router import router as annotations_router
from agentic_api.modules.documents.providers import DocumentsProvider
from agentic_api.modules.documents.router import router as documents_router
from agentic_api.modules.jobs.providers import JobsProvider
from agentic_api.modules.jobs.router import router as jobs_router
from agentic_api.modules.retrieval.providers import RetrievalProvider
from agentic_api.modules.retrieval.router import router as retrieval_router
from agentic_api.settings import load_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    container: AsyncContainer = app.state.dishka_container
    await container.close()


def create_app() -> FastAPI:
    settings = load_settings()
    container = make_service_container(
        AuthProvider(settings.auth, settings.role),
        DatabaseProvider(settings.database),
        LLMProvider(settings.llm),
        EmbeddingProvider(settings.llm, settings.embedding),
        StorageProvider(settings.minio),
        RedisProvider(settings.redis),
        QdrantProvider(settings.qdrant),
        infrastructure_health_provider(),
        AsyncDbProvider(settings.database),
        DocumentsProvider(),
        JobsProvider(settings.redis),
        RetrievalProvider(settings),
        AnnotationsProvider(),
    )
    app = create_fastapi_service_app(
        title="Squint API",
        description="Documents, indexing jobs, retrieval, and admin endpoints",
        log_level=settings.log_level,
        lifespan=lifespan,
    )
    apply_standard_http_middleware(app)
    register_domain_error_handlers(app)
    setup_dishka(container, app)
    app.include_router(health_router)
    app.include_router(documents_router, prefix="/v1")
    app.include_router(jobs_router, prefix="/v1")
    app.include_router(retrieval_router, prefix="/v1")
    app.include_router(annotations_router, prefix="/v1")
    return app


app = create_app()
