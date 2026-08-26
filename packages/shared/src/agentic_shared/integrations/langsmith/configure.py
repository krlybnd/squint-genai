"""Enable LangSmith tracing for LangGraph / LangChain when configured."""

from __future__ import annotations

import os

from agentic_shared.integrations.langsmith.settings import LangSmithSettings


def configure_langsmith(settings: LangSmithSettings) -> None:
    if not settings.enabled:
        os.environ.pop("LANGCHAIN_TRACING_V2", None)
        return
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = settings.project
    if settings.api_key:
        os.environ["LANGCHAIN_API_KEY"] = settings.api_key
    if settings.endpoint:
        os.environ["LANGCHAIN_ENDPOINT"] = settings.endpoint
