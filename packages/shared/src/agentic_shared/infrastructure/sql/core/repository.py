from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from agentic_shared.domains.persistence.entities.base import TenantScopedEntity


class SqlAlchemyReadRepository[T: TenantScopedEntity]:
    def __init__(
        self,
        session: AsyncSession,
        entity_type: type[T],
        tenant_id: str,
    ) -> None:
        self._session = session
        self._entity_type = entity_type
        self._tenant_id = tenant_id

    async def get_by_id(self, entity_id: UUID) -> T | None:
        result = await self._session.execute(
            select(self._entity_type).where(
                self._entity_type.id == entity_id,
                self._entity_type.tenant_id == self._tenant_id,
            )
        )
        return result.scalar_one_or_none()


class SqlAlchemyWriteRepository[T: TenantScopedEntity]:
    def __init__(
        self,
        session: AsyncSession,
        entity_type: type[T],
        tenant_id: str,
    ) -> None:
        self._session = session
        self._entity_type = entity_type
        self._tenant_id = tenant_id

    async def add(self, entity: T) -> T:
        if not entity.tenant_id:
            entity.tenant_id = self._tenant_id
        self._session.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def get_by_id(self, entity_id: UUID) -> T | None:
        entity = await self._session.get(self._entity_type, entity_id)
        if entity is None or entity.tenant_id != self._tenant_id:
            return None
        return entity

    async def update(self, entity: T) -> T:
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity_id: UUID) -> None:
        entity = await self.get_by_id(entity_id)
        if entity is None:
            return
        await self._session.delete(entity)
        await self._session.commit()


class SqlAlchemySyncWriteRepository[T: TenantScopedEntity]:
    def __init__(self, session: Session, entity_type: type[T], tenant_id: str) -> None:
        self._session = session
        self._entity_type = entity_type
        self._tenant_id = tenant_id

    def get_by_id(self, entity_id: UUID) -> T | None:
        entity = self._session.get(self._entity_type, entity_id)
        if entity is None or entity.tenant_id != self._tenant_id:
            return None
        return entity

    def update(self, entity: T) -> T:
        self._session.commit()
        self._session.refresh(entity)
        return entity
