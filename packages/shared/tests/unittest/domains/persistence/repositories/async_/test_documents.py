import unittest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.dml import Delete

from agentic_shared.domains.persistence.entities.document import Document
from agentic_shared.domains.persistence.entities.index_job import IndexJob
from agentic_shared.domains.persistence.repositories.async_.documents import (
    SqlAlchemyDocumentReadRepository,
    SqlAlchemyDocumentWriteRepository,
)


class _ScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None


class TestDocumentReadRepository(unittest.IsolatedAsyncioTestCase):
    async def test_list_ordered_by_created_desc_applies_limit_10(self) -> None:
        # Arrange
        captured: dict = {}

        class _Session:
            async def execute(self, stmt):
                captured["stmt"] = stmt
                return _ScalarResult([])

        repo = SqlAlchemyDocumentReadRepository(_Session(), "tenant-1")  # type: ignore[arg-type]

        # Act
        await repo.list_ordered_by_created_desc(limit=10)

        # Assert
        stmt = captured["stmt"]
        compiled = str(
            stmt.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )
        self.assertRegex(compiled.upper(), r"LIMIT\s+10")
        self.assertIn("tenant_id", compiled)
        self.assertIn("tenant-1", compiled)


class TestDocumentWriteRepository(unittest.IsolatedAsyncioTestCase):
    async def test_delete_cascades_index_jobs_before_document(self) -> None:
        # Arrange
        document_id = uuid4()
        document = Document(
            id=document_id,
            tenant_id="tenant-1",
            filename="doc.pdf",
            minio_key="doc.pdf",
        )
        executed: list = []

        class _Session:
            deleted: Document | None = None

            async def execute(self, stmt):
                executed.append(stmt)
                if len(executed) == 1:
                    return _ScalarResult([])
                return _ScalarResult([document])

            async def delete(self, entity: Document) -> None:
                self.deleted = entity

            async def commit(self):
                pass

        session = _Session()
        repo = SqlAlchemyDocumentWriteRepository(session, "tenant-1")  # type: ignore[arg-type]

        # Act
        await repo.delete(document_id)

        # Assert
        self.assertEqual(len(executed), 2)
        self.assertIsInstance(executed[0], Delete)
        self.assertEqual(executed[0].table, IndexJob.__table__)
        self.assertIs(session.deleted, document)

    async def test_delete_noops_when_document_missing(self) -> None:
        # Arrange
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[MagicMock(), _ScalarResult([])])
        session.delete = AsyncMock()
        session.commit = AsyncMock()
        repo = SqlAlchemyDocumentWriteRepository(session, "tenant-1")

        # Act
        await repo.delete(uuid4())

        # Assert
        session.delete.assert_not_awaited()
        session.commit.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
