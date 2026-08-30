from pydantic import Field

from agentic_shared.core.settings.base import EnvSettings


class FrameworkSettings(EnvSettings):
    """Base settings for HTTP/app framework knobs (CORS, middleware, …).

    Distinct from infrastructure (data plane) and integrations (external APIs).
    """

    title: str = Field(
        default="framework",
        description="Stable label for logs and readiness (not an env-driven resource name).",
    )
