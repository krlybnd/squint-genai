from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agentic_shared.core.auth.context import AuthContext
from agentic_shared.core.auth.tenant import resolve_tenant_id
from agentic_shared.domains.persistence.binder import RepositoryBinder
from agentic_shared.domains.persistence.protocols.chat import (
    ChatMessageReadRepository,
    ChatMessageWriteRepository,
    ChatSessionReadRepository,
    ChatSessionWriteRepository,
)
from agentic_shared.domains.persistence.protocols.documents import (
    DocumentReadRepository,
    DocumentWriteRepository,
)
from agentic_shared.domains.persistence.protocols.index_jobs import (
    IndexJobReadRepository,
    IndexJobWriteRepository,
)
from agentic_shared.domains.persistence.repositories.async_.chat import (
    SqlAlchemyChatMessageReadRepository,
    SqlAlchemyChatMessageWriteRepository,
    SqlAlchemyChatSessionReadRepository,
    SqlAlchemyChatSessionWriteRepository,
)
from agentic_shared.domains.persistence.repositories.async_.documents import (
    SqlAlchemyDocumentReadRepository,
    SqlAlchemyDocumentWriteRepository,
)
from agentic_shared.domains.persistence.repositories.async_.index_jobs import (
    SqlAlchemyIndexJobReadRepository,
    SqlAlchemyIndexJobWriteRepository,
)
from agentic_shared.infrastructure.postgres.session import create_session_factory
from agentic_shared.infrastructure.postgres.settings import DatabaseSettings


class AsyncDbProvider(Provider):
    """Session lifecycle + typed repository bindings via generic binder."""

    def __init__(self, settings: DatabaseSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.APP)
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        return create_session_factory(self._settings)

    @provide(scope=Scope.REQUEST)
    async def session(
        self, factory: async_sessionmaker[AsyncSession]
    ) -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def repository_binder(self, session: AsyncSession, auth: AuthContext) -> RepositoryBinder:
        return RepositoryBinder(session, resolve_tenant_id(auth))

    @provide(scope=Scope.REQUEST)
    def document_read_repository(self, binder: RepositoryBinder) -> DocumentReadRepository:
        return binder.bind(SqlAlchemyDocumentReadRepository)

    @provide(scope=Scope.REQUEST)
    def document_write_repository(self, binder: RepositoryBinder) -> DocumentWriteRepository:
        return binder.bind(SqlAlchemyDocumentWriteRepository)

    @provide(scope=Scope.REQUEST)
    def index_job_read_repository(self, binder: RepositoryBinder) -> IndexJobReadRepository:
        return binder.bind(SqlAlchemyIndexJobReadRepository)

    @provide(scope=Scope.REQUEST)
    def index_job_write_repository(self, binder: RepositoryBinder) -> IndexJobWriteRepository:
        return binder.bind(SqlAlchemyIndexJobWriteRepository)

    @provide(scope=Scope.REQUEST)
    def chat_session_read_repository(self, binder: RepositoryBinder) -> ChatSessionReadRepository:
        return binder.bind(SqlAlchemyChatSessionReadRepository)

    @provide(scope=Scope.REQUEST)
    def chat_session_write_repository(self, binder: RepositoryBinder) -> ChatSessionWriteRepository:
        return binder.bind(SqlAlchemyChatSessionWriteRepository)

    @provide(scope=Scope.REQUEST)
    def chat_message_read_repository(self, binder: RepositoryBinder) -> ChatMessageReadRepository:
        return binder.bind(SqlAlchemyChatMessageReadRepository)

    @provide(scope=Scope.REQUEST)
    def chat_message_write_repository(self, binder: RepositoryBinder) -> ChatMessageWriteRepository:
        return binder.bind(SqlAlchemyChatMessageWriteRepository)
