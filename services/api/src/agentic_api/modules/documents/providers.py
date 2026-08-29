from agentic_shared.core.auth.context import AuthContext
from agentic_shared.core.auth.tenant import resolve_tenant_id
from agentic_shared.domains.persistence.protocols.documents import (
    DocumentReadRepository,
    DocumentWriteRepository,
)
from agentic_shared.domains.persistence.protocols.index_jobs import (
    IndexJobReadRepository,
    IndexJobWriteRepository,
)
from agentic_shared.domains.retrieval.protocols.chunks import ChunkWriteRepository
from agentic_shared.infrastructure.object_storage.protocols import (
    ObjectStorageReader,
    ObjectStorageWriter,
)
from dishka import Provider, Scope, provide

from agentic_api.modules.documents.service import DocumentService
from agentic_api.modules.jobs.service import JobService


class DocumentsProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def document_service(
        self,
        auth: AuthContext,
        documents_read: DocumentReadRepository,
        documents_write: DocumentWriteRepository,
        jobs_read: IndexJobReadRepository,
        jobs_write: IndexJobWriteRepository,
        storage_read: ObjectStorageReader,
        storage_write: ObjectStorageWriter,
        chunk_write: ChunkWriteRepository,
        job_service: JobService,
    ) -> DocumentService:
        return DocumentService(
            resolve_tenant_id(auth),
            documents_read,
            documents_write,
            jobs_read,
            jobs_write,
            storage_read,
            storage_write,
            chunk_write,
            job_service,
        )
