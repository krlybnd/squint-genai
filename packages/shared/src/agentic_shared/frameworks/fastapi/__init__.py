"""FastAPI / Starlette adapters."""

from agentic_shared.frameworks.fastapi.auth.dependencies import require_roles
from agentic_shared.frameworks.fastapi.auth.middleware import SecurityHeadersMiddleware
from agentic_shared.frameworks.fastapi.health import router as health_router

__all__ = ["SecurityHeadersMiddleware", "health_router", "require_roles"]
