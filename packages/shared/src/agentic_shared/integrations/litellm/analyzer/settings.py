from pydantic import Field

from agentic_shared.integrations.core.settings import IntegrationSettings


class AnalyzerSettings(IntegrationSettings):
    """Analyzer sidecar (compose profile ``guardrails`` / Presidio analyzer)."""

    title: str = Field(
        default="analyzer",
        description="Readiness/log label for the analyzer client.",
    )
    analyzer_api_base: str = Field(
        default="http://localhost:5002",
        description="Analyzer base URL (host or docker DNS). Env: ANALYZER_API_BASE.",
    )
