from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from agentic_shared.domains.persistence.entities import Document, IndexJob
from agentic_shared.domains.persistence.limits import DEFAULT_LIST_LIMIT
from agentic_shared.infrastructure.postgres.repository import (
    SqlAlchemyReadRepository,
    SqlAlchemyWriteRepository,
)


class SqlAlchemyDocumentReadRepository(SqlAlchemyReadRepository[Document]):
    def __init__(self, session: AsyncSession, tenant_id: str) -> None:
        super().__init__(session, Document, tenant_id)

    async def list_ordered_by_created_desc(
        self, *, limit: int = DEFAULT_LIST_LIMIT
    ) -> list[Document]:
        result = await self._session.execute(
            select(Document)
            .where(Document.tenant_id == self._tenant_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class SqlAlchemyDocumentWriteRepository(SqlAlchemyWriteRepository[Document]):
    def __init__(self, session: AsyncSession, tenant_id: str) -> None:
        super().__init__(session, Document, tenant_id)

    async def delete(self, document_id: UUID) -> None:
        await self._session.execute(
            delete(IndexJob).where(
                IndexJob.document_id == document_id,
                IndexJob.tenant_id == self._tenant_id,
            )
        )
        result = await self._session.execute(
            select(Document).where(
                Document.id == document_id,
                Document.tenant_id == self._tenant_id,
            )
        )
        document = result.scalar_one_or_none()
        if document:
            await self._session.delete(document)
            await self._session.commit()
