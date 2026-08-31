"""Admin service entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from agentic_shared.frameworks.fastapi.dishka import make_service_container
from agentic_shared.frameworks.fastapi.framework import FastAPIAppBuilder
from agentic_shared.frameworks.fastapi.health import router as health_router
from agentic_shared.frameworks.fastapi.providers.auth import AuthProvider
from agentic_shared.integrations.idp.keycloak.providers import KeycloakAdminProvider
from dishka import AsyncContainer
from fastapi import FastAPI

from agentic_admin.modules.me.providers import MeProvider
from agentic_admin.modules.me.router import router as me_router
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
        MeProvider(),
    )
    return (
        FastAPIAppBuilder(
            settings.defaults.package,
            settings=settings.fastapi,
            log_level=settings.log_level,
        )
        .lifespan(lifespan)
        .with_standard_middleware()
        .with_dishka(container)
        .include_router(health_router)
        .include_router(me_router, prefix="/v1")
        .include_router(tenants_router, prefix="/v1")
        .include_router(users_router, prefix="/v1")
        .build()
    )


app = create_app()
