from agentic_shared.crosscut.auth.context import AuthContext
from agentic_shared.crosscut.auth.tenant import resolve_tenant_id
from agentic_shared.domains.persistence.protocols.documents import (
    DocumentReadRepository,
    DocumentWriteRepository,
)
from agentic_shared.domains.persistence.protocols.index_jobs import (
    IndexJobReadRepository,
    IndexJobWriteRepository,
)
from agentic_shared.infrastructure.cache.redis.settings import RedisSettings
from dishka import Provider, Scope, provide

from agentic_api.modules.jobs.service import JobService


class JobsProvider(Provider):
    def __init__(self, settings: RedisSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.REQUEST)
    def job_service(
        self,
        auth: AuthContext,
        documents_read: DocumentReadRepository,
        documents_write: DocumentWriteRepository,
        jobs_read: IndexJobReadRepository,
        jobs_write: IndexJobWriteRepository,
    ) -> JobService:
        return JobService(
            resolve_tenant_id(auth),
            documents_read,
            documents_write,
            jobs_read,
            jobs_write,
            self._settings,
        )
