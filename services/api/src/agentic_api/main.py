"""API service entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from agentic_shared.domains.persistence.providers import AsyncDbProvider
from agentic_shared.domains.pii_vault.providers import PiiVaultProvider
from agentic_shared.frameworks.fastapi.dishka import make_service_container
from agentic_shared.frameworks.fastapi.framework import FastAPIAppBuilder
from agentic_shared.frameworks.fastapi.health import router as health_router
from agentic_shared.frameworks.fastapi.middlewares.audit_unauthorized import (
    AuditUnauthorizedMiddleware,
)
from agentic_shared.frameworks.fastapi.providers.auth import AuthProvider
from agentic_shared.frameworks.fastapi.providers.compliance import ComplianceProvider
from agentic_shared.infrastructure.cache.redis.providers import RedisProvider
from agentic_shared.infrastructure.sql.postgres.providers import DatabaseProvider
from agentic_shared.infrastructure.storage.minio.providers import MinioProvider
from agentic_shared.infrastructure.vector.qdrant.providers import QdrantProvider
from agentic_shared.integrations.idp.keycloak.providers import KeycloakUserTenancyProvider
from agentic_shared.integrations.litellm.analyzer.providers import AnalyzerProvider
from agentic_shared.integrations.litellm.embedding.providers import EmbeddingProvider
from agentic_shared.integrations.litellm.guard.providers import GuardProvider
from agentic_shared.integrations.litellm.llm.providers import LLMProvider
from agentic_shared.integrations.litellm.rerank.providers import RerankProvider
from dishka import AsyncContainer
from fastapi import FastAPI

from agentic_api.modules.ai.providers import AiProvider
from agentic_api.modules.ai.router import router as ai_router
from agentic_api.modules.annotations.providers import AnnotationsProvider
from agentic_api.modules.annotations.router import router as annotations_router
from agentic_api.modules.documents.providers import DocumentsProvider
from agentic_api.modules.documents.router import router as documents_router
from agentic_api.modules.jobs.providers import JobsProvider
from agentic_api.modules.jobs.router import router as jobs_router
from agentic_api.modules.me.providers import MeProvider
from agentic_api.modules.me.router import router as me_router
from agentic_api.modules.retrieval.providers import RetrievalProvider
from agentic_api.modules.retrieval.router import router as retrieval_router
from agentic_api.modules.vault.providers import VaultApiProvider
from agentic_api.modules.vault.router import router as vault_router
from agentic_api.providers import resource_health_provider
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
        ComplianceProvider(settings.compliance, settings.database),
        KeycloakUserTenancyProvider(settings.keycloak_integration),
        DatabaseProvider(settings.database),
        LLMProvider(settings.llm),
        AnalyzerProvider(settings.analyzer),
        EmbeddingProvider(settings.llm, settings.embedding),
        GuardProvider(settings.guard),
        RerankProvider(settings.llm, settings.rerank),
        MinioProvider(settings.minio),
        RedisProvider(settings.redis),
        QdrantProvider(settings.qdrant),
        resource_health_provider(),
        AsyncDbProvider(settings.database),
        DocumentsProvider(),
        JobsProvider(settings.redis),
        RetrievalProvider(settings),
        AnnotationsProvider(),
        PiiVaultProvider(settings.crypto, settings.pii_vault),
        VaultApiProvider(),
        MeProvider(),
        AiProvider(),
    )
    app = (
        FastAPIAppBuilder(
            settings.defaults.package,
            settings=settings.fastapi,
            log_level=settings.log_level,
        )
        .lifespan(lifespan)
        .with_standard_middleware()
        .with_domain_errors()
        .with_dishka(container)
        .include_router(health_router)
        .include_router(me_router, prefix="/v1")
        .include_router(ai_router, prefix="/v1")
        .include_router(documents_router, prefix="/v1")
        .include_router(jobs_router, prefix="/v1")
        .include_router(retrieval_router, prefix="/v1")
        .include_router(vault_router, prefix="/v1")
        .include_router(annotations_router, prefix="/v1")
        .build()
    )
    app.add_middleware(AuditUnauthorizedMiddleware)
    return app


app = create_app()
