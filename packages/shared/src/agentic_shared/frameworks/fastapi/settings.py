"""FastAPI / Starlette HTTP framework settings (CORS, docs, middleware)."""

from pydantic import Field

from agentic_shared.frameworks.core.settings import FrameworkSettings
from agentic_shared.frameworks.fastapi.middlewares.security_headers_middleware.settings import (
    SecurityHeadersSettings,
)


class FastAPISettings(FrameworkSettings):
    """Env-tunable FastAPI knobs. Identity lives on ``PackageInfo``."""

    title: str = Field(
        default="fastapi",
        description="Log label for this framework settings slice.",
    )

    docs_url: str | None = Field(
        default="/docs",
        description="Swagger UI path. Empty string disables.",
    )
    redoc_url: str | None = Field(
        default="/redoc",
        description="ReDoc UI path. Empty string disables.",
    )
    openapi_url: str | None = Field(
        default="/openapi.json",
        description="OpenAPI JSON schema path. Empty string disables.",
    )

    cors_origins: str = Field(
        default=(
            "http://localhost:5173,http://localhost:5174,"
            "http://127.0.0.1:5173,http://127.0.0.1:5174,http://localhost"
        ),
        description=(
            "Comma-separated browser origins allowed with credentials. Must not include '*'."
        ),
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Send Access-Control-Allow-Credentials (cookies / auth headers).",
    )
    cors_allow_methods: str = Field(
        default="*",
        description="Comma-separated HTTP methods for CORS, or '*' for all.",
    )
    cors_allow_headers: str = Field(
        default="*",
        description="Comma-separated request headers for CORS, or '*' for all.",
    )

    security_headers: SecurityHeadersSettings = Field(
        default_factory=SecurityHeadersSettings,
        description="SecurityHeadersMiddleware toggle and header values.",
    )
