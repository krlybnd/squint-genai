"""Generic Alembic env — URL from DatabaseSettings (sync driver)."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from agentic_shared.domains.persistence.entities import Base
from agentic_shared.domains.persistence.entities import chat as _chat  # noqa: F401
from agentic_shared.domains.persistence.entities import document as _document  # noqa: F401
from agentic_shared.domains.persistence.entities import index_job as _index_job  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    from agentic_shared.infrastructure.sql.postgres.settings import DatabaseSettings

    return DatabaseSettings().sqlalchemy_psycopg2_url()


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
