"""LangSmith tracing bootstrap for LangGraph (chat service only)."""

from __future__ import annotations

import os

from agentic_shared.core.settings.base import EnvSettings
from agentic_shared.core.settings.secrets import SecuredStr
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class LangSmithTracingSettings(EnvSettings):
    """Optional LangSmith / LangChain tracing env for chat graph runs."""

    model_config = SettingsConfigDict(env_prefix="LANGSMITH_", env_file=".env", extra="ignore")

    enabled: bool = Field(
        default=False,
        description="When true, set LANGCHAIN_TRACING_V2 and related env for LangGraph.",
    )
    api_key: SecuredStr = Field(
        default=SecuredStr(""),
        description="LangSmith API key (LANGSMITH_API_KEY → LANGCHAIN_API_KEY).",
    )
    project: str = Field(
        default="agentic-rag-eval",
        description="LangSmith project name for traced runs.",
    )
    endpoint: str = Field(
        default="https://api.smith.langchain.com",
        description="LangSmith API endpoint URL.",
    )


def configure_langsmith_tracing(settings: LangSmithTracingSettings) -> None:
    if not settings.enabled:
        os.environ.pop("LANGCHAIN_TRACING_V2", None)
        return
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = settings.project
    api_key = settings.api_key.get_secret_value()
    if api_key:
        os.environ["LANGCHAIN_API_KEY"] = api_key
    if settings.endpoint:
        os.environ["LANGCHAIN_ENDPOINT"] = settings.endpoint
