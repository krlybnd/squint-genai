from collections.abc import Callable
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

R = TypeVar("R")


class RepositoryBinder:
    """Request-scoped factory for SQLAlchemy domain repositories."""

    def __init__(self, session: AsyncSession, tenant_id: str) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def bind(self, repo_cls: Callable[[AsyncSession, str], R]) -> R:
        return repo_cls(self._session, self._tenant_id)
