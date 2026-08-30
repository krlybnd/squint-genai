"""FastAPI / Starlette adapters."""

from agentic_shared.frameworks.fastapi.defaults import FrameworkDefaults
from agentic_shared.frameworks.fastapi.dependencies.auth.dependency import require_roles
from agentic_shared.frameworks.fastapi.dishka import make_service_container
from agentic_shared.frameworks.fastapi.framework import FastAPIAppBuilder
from agentic_shared.frameworks.fastapi.health import router as health_router
from agentic_shared.frameworks.fastapi.middlewares.security_headers_middleware.middleware import (
    SecurityHeadersMiddleware,
)
from agentic_shared.frameworks.fastapi.providers.auth import AuthProvider
from agentic_shared.frameworks.fastapi.settings import FastAPISettings

__all__ = [
    "AuthProvider",
    "FastAPIAppBuilder",
    "FastAPISettings",
    "FrameworkDefaults",
    "SecurityHeadersMiddleware",
    "health_router",
    "make_service_container",
    "require_roles",
]
