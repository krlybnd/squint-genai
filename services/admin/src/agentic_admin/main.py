from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from agentic_shared.core.auth.providers import AuthProvider
from agentic_shared.core.ioc.container import make_service_container
from agentic_shared.frameworks.fastapi.bootstrap import (
    apply_standard_http_middleware,
    create_fastapi_service_app,
)
from agentic_shared.frameworks.fastapi.health import router as health_router
from agentic_shared.integrations.keycloak_admin.providers import KeycloakAdminProvider
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from agentic_admin.modules.tenants.providers import TenantsProvider
from agentic_admin.modules.tenants.router import router as tenants_router
from agentic_admin.modules.users.providers import UsersProvider
from agentic_admin.modules.users.router import router as users_router
from agentic_admin.settings import load_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    container: AsyncContainer = app.state.dishka_container
    await container.close()


def create_app() -> FastAPI:
    settings = load_settings()
    container = make_service_container(
        AuthProvider(settings.auth, settings.role),
        KeycloakAdminProvider(settings.keycloak_integration),
        TenantsProvider(),
        UsersProvider(),
    )
    app = create_fastapi_service_app(
        title="Squint Admin API",
        description="Tenant and user administration (Keycloak Organizations)",
        log_level=settings.log_level,
        lifespan=lifespan,
    )
    apply_standard_http_middleware(app)
    setup_dishka(container, app)
    app.include_router(health_router)
    app.include_router(tenants_router, prefix="/v1")
    app.include_router(users_router, prefix="/v1")
    return app


app = create_app()
