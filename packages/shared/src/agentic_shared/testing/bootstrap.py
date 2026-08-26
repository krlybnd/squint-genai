"""Safe default env for unit tests — imported from tests/unittest/conftest.py."""

from __future__ import annotations

import os


def apply_test_env() -> None:
    """Apply deterministic defaults without overriding explicit env."""
    defaults = {
        "AUTH_MODE": "none",
        "DATABASE_URL": "postgresql+asyncpg://agentic:agentic@localhost:5432/agentic_rag_eval_test",
        "REDIS_URL": "redis://localhost:6379/0",
        "CELERY_BROKER_URL": "redis://localhost:6379/0",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/1",
        "MINIO_ENDPOINT": "localhost:9000",
        "MINIO_ACCESS_KEY": "minioadmin",
        "MINIO_SECRET_KEY": "minioadmin",
        "MINIO_BUCKET": "documents-test",
        "MINIO_SECURE": "false",
        "QDRANT_URL": "http://localhost:6333",
        "QDRANT_COLLECTION": "agentic_rag_eval_test",
        "LITELLM_BASE_URL": "http://localhost:4000",
        "LITELLM_MODEL": "gpt-4o-mini",
        "OPENAI_API_KEY": "test-key",
        "RERANK_ENABLED": "false",
        "DEEPEVAL_TELEMETRY_OPT_OUT": "YES",
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)
