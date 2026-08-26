"""Browser CORS origins — never wildcard when credentials are enabled."""

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from agentic_shared.core.settings.base import EnvSettings

_DEFAULT_ORIGINS = (
    "http://localhost:5173,"
    "http://localhost:5174,"
    "http://127.0.0.1:5173,"
    "http://127.0.0.1:5174,"
    "http://localhost"
)


class CorsSettings(EnvSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cors_origins: str = Field(default=_DEFAULT_ORIGINS)
    cors_allow_credentials: bool = True

    def origin_list(self) -> list[str]:
        origins = [part.strip() for part in self.cors_origins.split(",") if part.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS must list at least one origin")
        if "*" in origins:
            raise ValueError(
                "CORS_ORIGINS cannot include '*'; browsers reject wildcard with credentials"
            )
        return origins
