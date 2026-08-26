from sqlalchemy.engine import URL, make_url


def parse_database_url(url: str) -> URL:
    return make_url(url)


def assert_asyncpg_driver(database_url: str) -> None:
    driver = parse_database_url(database_url).drivername
    if "asyncpg" not in driver:
        raise ValueError(
            f"database_url must use the asyncpg driver (got {driver!r}). "
            "Example: postgresql+asyncpg://user:pass@host:5432/db"
        )


def sqlalchemy_psycopg2_url(source: str) -> str:
    parsed = parse_database_url(source)
    return parsed.set(drivername="postgresql+psycopg2").render_as_string(hide_password=False)


def libpq_postgres_url(source: str) -> str:
    """Plain ``postgresql://`` for libpq / psycopg-style consumers (e.g. LangGraph checkpoint)."""
    parsed = parse_database_url(source)
    return parsed.set(drivername="postgresql").render_as_string(hide_password=False)


def assert_psycopg_driver(url: str) -> None:
    driver = parse_database_url(url).drivername
    if "psycopg" not in driver:
        raise ValueError(
            f"Sync SQLAlchemy URL must use psycopg2/psycopg (got {driver!r}). "
            "Set DATABASE_URL_PSYCOPG2 or derive from DATABASE_URL."
        )


def assert_libpq_postgres_url(url: str) -> None:
    driver = parse_database_url(url).drivername
    if driver not in ("postgresql", "postgres"):
        raise ValueError(
            f"Checkpoint URL must be plain postgresql:// (got {driver!r}). "
            "Set CHECKPOINT_DATABASE_URL or derive from DATABASE_URL."
        )
