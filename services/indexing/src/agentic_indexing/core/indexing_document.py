import logging
import uuid
from datetime import UTC, datetime

from agentic_shared.domains.indexing.models import IndexDocumentTaskResult
from agentic_shared.domains.persistence.entities import JobStatus
from agentic_shared.domains.persistence.protocols.documents import DocumentWriteRepositorySync
from agentic_shared.domains.persistence.protocols.index_jobs import IndexJobWriteRepositorySync
from agentic_shared.infrastructure.object_storage.protocols import ObjectStorageReader
from agentic_shared.infrastructure.vector.protocols import QdrantWriter
from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm.settings import LLMSettings

from agentic_indexing.modules.pdf_indexing.pipeline import index_pdf_bytes

logger = logging.getLogger(__name__)


class IndexDocumentUseCase:
    def __init__(
        self,
        *,
        jobs: IndexJobWriteRepositorySync,
        documents: DocumentWriteRepositorySync,
        storage_read: ObjectStorageReader,
        qdrant_write: QdrantWriter,
        llm: LLMSettings,
        embedding: EmbeddingSettings,
    ) -> None:
        self._jobs = jobs
        self._documents = documents
        self._storage_read = storage_read
        self._qdrant_write = qdrant_write
        self._llm = llm
        self._embedding = embedding

    def run(
        self,
        *,
        job_id: uuid.UUID,
        document_id: uuid.UUID,
        minio_key: str,
        filename: str,
        tenant_id: str,
        mark_running: bool,
    ) -> IndexDocumentTaskResult:
        if mark_running:
            self._jobs.update_status(job_id, JobStatus.RUNNING)

        logger.debug("downloading document minio_key=%s job_id=%s", minio_key, job_id)
        pdf_bytes = self._storage_read.download(minio_key)
        logger.debug("downloaded document bytes=%d job_id=%s", len(pdf_bytes), job_id)
        chunk_count = index_pdf_bytes(
            pdf_bytes,
            doc_id=str(document_id),
            source_file=filename,
            tenant_id=tenant_id,
            qdrant_write=self._qdrant_write,
            llm=self._llm,
            embedding=self._embedding,
        )

        document = self._documents.get_by_id(document_id)
        if document:
            document.indexed_at = datetime.now(UTC)
            self._documents.update(document)

        self._jobs.update_status(job_id, JobStatus.COMPLETED)
        logger.info(
            "index completed job_id=%s document_id=%s chunks=%d tenant_id=%s",
            job_id,
            document_id,
            chunk_count,
            tenant_id,
        )
        return IndexDocumentTaskResult.from_run(document_id=document_id, chunk_count=chunk_count)
