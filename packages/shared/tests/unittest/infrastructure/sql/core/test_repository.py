import unittest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from agentic_shared.domains.persistence.entities.document import Document
from agentic_shared.infrastructure.sql.core.repository import (
    SqlAlchemyReadRepository,
    SqlAlchemyWriteRepository,
)


class TestSqlAlchemyReadRepository(unittest.IsolatedAsyncioTestCase):
    async def test_get_by_id_scopes_to_tenant(self) -> None:
        # Arrange
        entity_id = uuid4()
        document = Document(
            id=entity_id,
            tenant_id="tenant-a",
            filename="a.pdf",
            minio_key="a.pdf",
        )
        result = MagicMock()
        result.scalar_one_or_none.return_value = document
        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)
        repo = SqlAlchemyReadRepository(session, Document, "tenant-a")

        # Act
        found = await repo.get_by_id(entity_id)

        # Assert
        session.execute.assert_awaited_once()
        self.assertIs(found, document)


class TestSqlAlchemyWriteRepository(unittest.IsolatedAsyncioTestCase):
    async def test_add_sets_tenant_id_when_missing(self) -> None:
        # Arrange
        entity = Document(
            id=uuid4(),
            tenant_id="",
            filename="doc.pdf",
            minio_key="doc.pdf",
        )
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        repo = SqlAlchemyWriteRepository(session, Document, "tenant-b")

        # Act
        out = await repo.add(entity)

        # Assert
        self.assertEqual(entity.tenant_id, "tenant-b")
        session.add.assert_called_once_with(entity)
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(entity)
        self.assertIs(out, entity)

    async def test_delete_skips_when_tenant_mismatch(self) -> None:
        # Arrange
        entity_id = uuid4()
        entity = Document(
            id=entity_id,
            tenant_id="other-tenant",
            filename="doc.pdf",
            minio_key="doc.pdf",
        )
        session = AsyncMock()
        session.get = AsyncMock(return_value=entity)
        session.delete = AsyncMock()
        session.commit = AsyncMock()
        repo = SqlAlchemyWriteRepository(session, Document, "tenant-a")

        # Act
        await repo.delete(entity_id)

        # Assert
        session.get.assert_awaited_once_with(Document, entity_id)
        session.delete.assert_not_awaited()
        session.commit.assert_not_awaited()

    async def test_delete_removes_matching_tenant_entity(self) -> None:
        # Arrange
        entity_id = uuid4()
        entity = Document(
            id=entity_id,
            tenant_id="tenant-a",
            filename="doc.pdf",
            minio_key="doc.pdf",
        )
        session = AsyncMock()
        session.get = AsyncMock(return_value=entity)
        session.delete = AsyncMock()
        session.commit = AsyncMock()
        repo = SqlAlchemyWriteRepository(session, Document, "tenant-a")

        # Act
        await repo.delete(entity_id)

        # Assert
        session.delete.assert_awaited_once_with(entity)
        session.commit.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
