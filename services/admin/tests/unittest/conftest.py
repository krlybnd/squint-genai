"""Unit test env defaults."""

from __future__ import annotations

import os


def apply_test_env() -> None:
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
        "LITELLM_MODEL": "generate",
        "LITELLM_ROUTER_MODEL": "router",
        "LITELLM_JUDGE_MODEL": "judge",
        "LITELLM_MASTER_KEY": "test-key",
        "EMBEDDING_MODEL": "embed",
        "DEEPEVAL_TELEMETRY_OPT_OUT": "YES",
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)


apply_test_env()
