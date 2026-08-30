from pydantic import Field

from agentic_shared.infrastructure.core.settings import InfraSettings


class RedisSettings(InfraSettings):
    """Redis for cache and Celery broker/result backends."""

    title: str = Field(default="redis", description="Readiness/log label for the Redis client.")
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL used by the application cache client.",
    )
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL (task queue).",
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/1",
        description="Celery result backend URL (task results; often a separate DB index).",
    )
