from typing import Self

from pydantic import model_validator

from agentic_shared.infrastructure.core.settings import InfraSettings
from agentic_shared.infrastructure.postgres.urls import (
    assert_asyncpg_driver,
    assert_libpq_postgres_url,
    assert_psycopg_driver,
    libpq_postgres_url,
    sqlalchemy_psycopg2_url,
)


class DatabaseSettings(InfraSettings):
    title: str = "postgresql"
    database_url: str = "postgresql+asyncpg://agentic:agentic@localhost:5432/agentic_rag_eval"
    database_url_psycopg2: str | None = None
    checkpoint_database_url: str | None = None

    @model_validator(mode="after")
    def _validate_database_urls(self) -> Self:
        assert_asyncpg_driver(self.database_url)
        if self.database_url_psycopg2 is not None:
            assert_psycopg_driver(self.database_url_psycopg2)
        if self.checkpoint_database_url is not None:
            assert_libpq_postgres_url(self.checkpoint_database_url)
        return self

    def sqlalchemy_psycopg2_url(self) -> str:
        if self.database_url_psycopg2 is not None:
            return self.database_url_psycopg2
        return sqlalchemy_psycopg2_url(self.database_url)

    def checkpoint_postgres_url(self) -> str:
        if self.checkpoint_database_url is not None:
            return self.checkpoint_database_url
        return libpq_postgres_url(self.database_url)
