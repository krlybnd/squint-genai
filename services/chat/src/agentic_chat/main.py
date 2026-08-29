from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from agentic_shared.core.health.providers import make_resource_health_provider
from agentic_shared.core.ioc import AuthProvider, DatabaseProvider, LLMProvider
from agentic_shared.core.ioc.container import make_service_container
from agentic_shared.domains.persistence.providers import AsyncDbProvider
from agentic_shared.domains.retrieval.providers import AsyncRetrievalProvider
from agentic_shared.frameworks.fastapi.bootstrap import (
    apply_standard_http_middleware,
    create_fastapi_service_app,
)
from agentic_shared.frameworks.fastapi.domain_errors import register_domain_error_handlers
from agentic_shared.frameworks.fastapi.health import router as health_router
from agentic_shared.infrastructure.postgres.client import DatabaseClient
from agentic_shared.infrastructure.vector.providers import QdrantProvider
from agentic_shared.integrations.langsmith.configure import configure_langsmith
from agentic_shared.integrations.llm.protocols import ChatClient
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from agentic_chat.core.graph import close_checkpointer
from agentic_chat.modules.chat.providers import ChatProvider
from agentic_chat.modules.chat.router import router as chat_router
from agentic_chat.settings import load_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await close_checkpointer()
    container: AsyncContainer = app.state.dishka_container
    await container.close()


def create_app() -> FastAPI:
    settings = load_settings()
    configure_langsmith(settings.langsmith)
    container = make_service_container(
        AuthProvider(settings.auth, settings.role),
        DatabaseProvider(settings.database),
        LLMProvider(settings.llm),
        make_resource_health_provider(DatabaseClient, ChatClient),
        QdrantProvider(settings.qdrant),
        AsyncDbProvider(settings.database),
        AsyncRetrievalProvider(
            settings.llm,
            settings.embedding,
            settings.rerank,
        ),
        ChatProvider(settings),
    )
    app = create_fastapi_service_app(
        title="Squint Chat",
        description="Stateful chat with LangGraph workflow + SSE streaming",
        log_level=settings.log_level,
        lifespan=lifespan,
    )
    apply_standard_http_middleware(app)
    register_domain_error_handlers(app)
    setup_dishka(container, app)
    app.include_router(health_router)
    app.include_router(chat_router)
    return app


app = create_app()
