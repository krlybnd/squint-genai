import logging
import uuid
from datetime import UTC, datetime

from agentic_shared.domains.indexing.models import IndexDocumentTaskResult
from agentic_shared.domains.persistence.entities import JobStatus
from agentic_shared.domains.persistence.protocols.documents import DocumentWriteRepositorySync
from agentic_shared.domains.persistence.protocols.index_jobs import IndexJobWriteRepositorySync
from agentic_shared.domains.pii_vault.protocols import IndexTimePiiTokenizationPort
from agentic_shared.domains.retrieval.protocols.chunks import ChunkWriteRepository
from agentic_shared.infrastructure.storage.core.protocols import StorageReader
from agentic_shared.integrations.litellm.embedding.settings import LiteLLMEmbeddingSettings
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings

from agentic_indexing.modules.pdf_indexing.pipeline import index_pdf_bytes

logger = logging.getLogger(__name__)


class IndexDocumentUseCase:
    def __init__(
        self,
        *,
        jobs: IndexJobWriteRepositorySync,
        documents: DocumentWriteRepositorySync,
        storage_read: StorageReader,
        chunk_write: ChunkWriteRepository,
        llm: LiteLLMChatSettings,
        embedding: LiteLLMEmbeddingSettings,
        pii: IndexTimePiiTokenizationPort | None = None,
    ) -> None:
        self._jobs = jobs
        self._documents = documents
        self._storage_read = storage_read
        self._chunk_write = chunk_write
        self._llm = llm
        self._embedding = embedding
        self._pii = pii

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
        self._chunk_write.delete_by_doc_id(str(document_id), tenant_id=tenant_id)
        chunk_count = index_pdf_bytes(
            pdf_bytes,
            doc_id=str(document_id),
            source_file=filename,
            tenant_id=tenant_id,
            chunk_write=self._chunk_write,
            llm=self._llm,
            embedding=self._embedding,
            pii=self._pii,
            doc_uuid=document_id,
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

    def close(self) -> None:
        if self._pii is not None:
            self._pii.close()
