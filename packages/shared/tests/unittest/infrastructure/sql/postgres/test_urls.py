import unittest

from agentic_shared.infrastructure.sql.postgres.settings import DatabaseSettings
from agentic_shared.infrastructure.sql.postgres.urls import (
    assert_asyncpg_driver,
    assert_libpq_postgres_url,
    assert_psycopg_driver,
    libpq_postgres_url,
    sqlalchemy_psycopg2_url,
)


class TestDatabaseUrls(unittest.TestCase):
    def test_database_settings_derives_sync_and_checkpoint_urls(self) -> None:
        # Arrange
        db = DatabaseSettings(
            database_url="postgresql+asyncpg://u:p@db:5432/app",
        )

        # Assert
        self.assertEqual(db.sqlalchemy_psycopg2_url(), "postgresql+psycopg2://u:p@db:5432/app")
        self.assertEqual(db.checkpoint_postgres_url(), "postgresql://u:p@db:5432/app")

    def test_database_settings_explicit_overrides(self) -> None:
        # Arrange
        db = DatabaseSettings(
            database_url="postgresql+asyncpg://u:p@db:5432/app",
            database_url_psycopg2="postgresql+psycopg2://sync:sync@other:5432/app",
            checkpoint_database_url="postgresql://cp:cp@checkpoint:5432/app",
        )

        # Assert
        self.assertIn("sync@other", db.sqlalchemy_psycopg2_url())
        self.assertTrue(db.checkpoint_postgres_url().startswith("postgresql://cp:"))

    def test_database_url_must_be_asyncpg(self) -> None:
        # Act / Assert
        with self.assertRaises(ValueError):
            DatabaseSettings(database_url="postgresql+psycopg2://u:p@localhost/db")

    def test_assert_asyncpg_driver(self) -> None:
        # Act / Assert
        assert_asyncpg_driver("postgresql+asyncpg://localhost/db")
        with self.assertRaises(ValueError):
            assert_asyncpg_driver("postgresql://localhost/db")

    def test_sqlalchemy_psycopg2_url_rewrites_driver(self) -> None:
        # Arrange
        source = "postgresql+asyncpg://user:pass@db:5432/app"

        # Act / Assert
        self.assertEqual(
            sqlalchemy_psycopg2_url(source),
            "postgresql+psycopg2://user:pass@db:5432/app",
        )

    def test_libpq_postgres_url_strips_asyncpg_driver(self) -> None:
        # Arrange
        source = "postgresql+asyncpg://user:pass@db:5432/app"

        # Act / Assert
        self.assertEqual(libpq_postgres_url(source), "postgresql://user:pass@db:5432/app")

    def test_assert_psycopg_driver(self) -> None:
        # Act / Assert
        assert_psycopg_driver("postgresql+psycopg2://localhost/db")
        with self.assertRaises(ValueError):
            assert_psycopg_driver("postgresql+asyncpg://localhost/db")

    def test_assert_libpq_postgres_url(self) -> None:
        # Act / Assert
        assert_libpq_postgres_url("postgresql://localhost/db")
        with self.assertRaises(ValueError):
            assert_libpq_postgres_url("postgresql+asyncpg://localhost/db")


if __name__ == "__main__":
    unittest.main()
