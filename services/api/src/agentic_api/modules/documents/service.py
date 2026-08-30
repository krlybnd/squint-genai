import logging
import uuid

from agentic_shared.domains.domain_errors import BadRequestError, ConflictError, NotFoundError
from agentic_shared.domains.persistence.entities import Document, IndexJob, JobStatus
from agentic_shared.domains.persistence.protocols.documents import (
    DocumentReadRepository,
    DocumentWriteRepository,
)
from agentic_shared.domains.persistence.protocols.index_jobs import (
    IndexJobReadRepository,
    IndexJobWriteRepository,
)
from agentic_shared.domains.retrieval.protocols.chunks import ChunkWriteRepository
from agentic_shared.infrastructure.storage.core.protocols import (
    StorageReader,
    StorageWriter,
)

from agentic_api.modules.documents.schemas import DocumentOut, IndexStatus
from agentic_api.modules.jobs.service import JobService

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(
        self,
        tenant_id: str,
        documents_read: DocumentReadRepository,
        documents_write: DocumentWriteRepository,
        jobs_read: IndexJobReadRepository,
        jobs_write: IndexJobWriteRepository,
        storage_read: StorageReader,
        storage_write: StorageWriter,
        chunk_write: ChunkWriteRepository,
        job_service: JobService,
    ) -> None:
        self._tenant_id = tenant_id
        self._documents_read = documents_read
        self._documents_write = documents_write
        self._jobs_read = jobs_read
        self._jobs_write = jobs_write
        self._storage_read = storage_read
        self._storage_write = storage_write
        self._chunk_write = chunk_write
        self._job_service = job_service

    async def create_upload_presign(
        self,
        filename: str,
    ) -> tuple[Document, int]:
        doc_id = uuid.uuid4()
        minio_key = f"pdfs/{self._tenant_id}/{doc_id}/{filename}"
        document = Document(
            id=doc_id,
            tenant_id=self._tenant_id,
            filename=filename,
            minio_key=minio_key,
        )
        document = await self._documents_write.add(document)
        logger.info(
            "presign created document_id=%s filename=%s tenant_id=%s",
            doc_id,
            filename,
            self._tenant_id,
        )
        return document, 3600

    async def upload_bytes(self, document_id: uuid.UUID, data: bytes) -> Document:
        document = await self._documents_read.get_by_id(document_id)
        if not document:
            raise NotFoundError("Document not found")
        if not data:
            raise BadRequestError("Empty file")
        self._storage_write.upload(document.minio_key, data)
        logger.info(
            "uploaded bytes document_id=%s size=%d tenant_id=%s",
            document_id,
            len(data),
            self._tenant_id,
        )
        return document

    async def complete_upload(self, document_id: uuid.UUID) -> tuple[Document, IndexJob]:
        document = await self._documents_read.get_by_id(document_id)
        if not document:
            raise NotFoundError("Document not found")
        if not self._storage_read.object_exists(document.minio_key):
            raise BadRequestError("Object not found in MinIO — upload the file first")

        if await self._jobs_read.find_active_for_document(document_id):
            raise ConflictError("Indexing job already queued for this document")

        job = IndexJob(
            tenant_id=self._tenant_id,
            document_id=document_id,
            status=JobStatus.PENDING,
        )
        job = await self._jobs_write.add(job)
        logger.info(
            "upload completed document_id=%s job_id=%s tenant_id=%s",
            document_id,
            job.id,
            self._tenant_id,
        )
        return document, job

    async def reindex_document(self, document_id: uuid.UUID) -> tuple[Document, IndexJob]:
        document = await self._documents_read.get_by_id(document_id)
        if not document:
            raise NotFoundError("Document not found")
        if not self._storage_read.object_exists(document.minio_key):
            raise BadRequestError("Object not found in MinIO — upload the file first")

        await self._job_service.cancel_indexing_for_document(document_id)
        self._chunk_write.delete_by_doc_id(
            str(document_id),
            tenant_id=self._tenant_id,
        )
        document.indexed_at = None
        await self._documents_write.update(document)
        job = IndexJob(
            tenant_id=self._tenant_id,
            document_id=document_id,
            status=JobStatus.PENDING,
        )
        job = await self._jobs_write.add(job)
        await self._job_service.enqueue_index_job(
            job.id, document.id, document.minio_key, document.filename, self._tenant_id
        )
        logger.info(
            "reindex queued document_id=%s job_id=%s tenant_id=%s",
            document_id,
            job.id,
            self._tenant_id,
        )
        return document, job

    async def delete_document(self, document_id: uuid.UUID) -> None:
        document = await self._documents_read.get_by_id(document_id)
        if not document:
            raise NotFoundError("Document not found")
        await self._job_service.cancel_indexing_for_document(document_id)
        self._chunk_write.delete_by_doc_id(
            str(document_id),
            tenant_id=self._tenant_id,
        )
        if self._storage_read.object_exists(document.minio_key):
            self._storage_write.delete(document.minio_key)
        await self._documents_write.delete(document_id)
        logger.info("deleted document document_id=%s tenant_id=%s", document_id, self._tenant_id)

    async def list_documents(self) -> list[DocumentOut]:
        rows = await self._documents_read.list_ordered_by_created_desc()
        items: list[DocumentOut] = []
        for document in rows:
            items.append(await self._to_document_out(document))
        return items

    async def get(self, document_id: uuid.UUID) -> Document | None:
        return await self._documents_read.get_by_id(document_id)

    async def get_out(self, document_id: uuid.UUID) -> DocumentOut | None:
        document = await self._documents_read.get_by_id(document_id)
        if not document:
            return None
        return await self._to_document_out(document)

    async def _to_document_out(self, document: Document) -> DocumentOut:
        status = await self._resolve_index_status(document)
        return DocumentOut(
            id=document.id,
            filename=document.filename,
            minio_key=document.minio_key,
            page_count=document.page_count,
            indexed_at=document.indexed_at,
            index_status=status,
            created_at=document.created_at,
        )

    async def _resolve_index_status(self, document: Document) -> IndexStatus:
        if document.indexed_at:
            return IndexStatus.INDEXED
        active = await self._jobs_read.find_active_for_document(document.id)
        if active:
            return IndexStatus.INDEXING
        latest = await self._jobs_read.get_latest_for_document(document.id)
        if latest and latest.status == JobStatus.FAILED:
            return IndexStatus.FAILED
        return IndexStatus.PENDING
