from agentic_shared.infrastructure.core.settings import InfraSettings


class RedisSettings(InfraSettings):
    title: str = "redis"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
