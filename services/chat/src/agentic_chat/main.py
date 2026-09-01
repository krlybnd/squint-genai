"""Chat service entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from agentic_shared.core.health.providers import make_resource_health_provider
from agentic_shared.domains.persistence.providers import AsyncDbProvider
from agentic_shared.domains.pii_vault.providers import PiiVaultProvider
from agentic_shared.domains.retrieval.providers import AsyncRetrievalProvider
from agentic_shared.frameworks.fastapi.dishka import make_service_container
from agentic_shared.frameworks.fastapi.framework import FastAPIAppBuilder
from agentic_shared.frameworks.fastapi.health import router as health_router
from agentic_shared.frameworks.fastapi.providers.auth import AuthProvider
from agentic_shared.infrastructure.sql.postgres.client import DatabaseClient
from agentic_shared.infrastructure.sql.postgres.providers import DatabaseProvider
from agentic_shared.infrastructure.vector.qdrant.providers import QdrantProvider
from agentic_shared.integrations.litellm.analyzer.providers import AnalyzerProvider
from agentic_shared.integrations.litellm.anonymizer.providers import AnonymizerProvider
from agentic_shared.integrations.litellm.guard.providers import GuardProvider
from agentic_shared.integrations.litellm.llm.protocols import ChatClient
from agentic_shared.integrations.litellm.llm.providers import LLMProvider
from agentic_shared.integrations.litellm.rerank.providers import RerankProvider
from dishka import AsyncContainer
from fastapi import FastAPI

from agentic_chat.core.graph import close_checkpointer
from agentic_chat.modules.chat.providers import ChatProvider
from agentic_chat.modules.chat.router import router as chat_router
from agentic_chat.settings import load_settings
from agentic_chat.tracing import configure_langsmith_tracing


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await close_checkpointer()
    container: AsyncContainer = app.state.dishka_container
    await container.close()


def create_app() -> FastAPI:
    settings = load_settings()
    configure_langsmith_tracing(settings.langsmith)
    container = make_service_container(
        AuthProvider(settings.auth, settings.role),
        DatabaseProvider(settings.database),
        LLMProvider(settings.llm),
        AnalyzerProvider(settings.analyzer),
        AnonymizerProvider(settings.anonymizer),
        GuardProvider(settings.guard),
        RerankProvider(settings.llm, settings.rerank),
        make_resource_health_provider(DatabaseClient, ChatClient),
        QdrantProvider(settings.qdrant),
        AsyncDbProvider(settings.database),
        AsyncRetrievalProvider(
            settings.llm,
            settings.embedding,
        ),
        PiiVaultProvider(settings.crypto, settings.pii_vault),
        ChatProvider(settings),
    )
    return (
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
        .include_router(chat_router)
        .build()
    )


app = create_app()
