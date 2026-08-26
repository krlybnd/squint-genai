import logging
import uuid

from agentic_shared.core.banner import print_startup_banner
from agentic_shared.core.logging import setup_logging
from agentic_shared.domains.persistence.entities import JobStatus
from agentic_shared.domains.persistence.repositories.sync_.documents import (
    SqlAlchemyDocumentWriteRepositorySync,
    SqlAlchemyIndexJobWriteRepositorySync,
)
from agentic_shared.infrastructure.object_storage.client import (
    MinioClient,
    MinioObjectStorageReader,
)
from agentic_shared.infrastructure.vector.client import QdrantClient, QdrantVectorWriter
from celery import Celery
from celery.signals import after_setup_logger, worker_ready
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agentic_indexing.core.indexing_document import IndexDocumentUseCase
from agentic_indexing.settings import IndexingSettings, load_settings

_settings = load_settings()
logger = logging.getLogger(__name__)

celery_app = Celery(
    "agentic_indexing",
    broker=_settings.redis.celery_broker_url,
    backend=_settings.redis.celery_result_backend,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
)


@after_setup_logger.connect
def _on_celery_logger_setup(**_kwargs: object) -> None:
    setup_logging(_settings.log_level)


@worker_ready.connect
def _on_worker_ready(**_kwargs: object) -> None:
    setup_logging(_settings.log_level)
    print_startup_banner("Squint Indexing Worker")


engine = create_engine(_settings.database.sqlalchemy_psycopg2_url())
SessionLocal = sessionmaker(bind=engine)


def _build_use_case(
    session: Session,
    tenant_id: str,
    *,
    minio: MinioClient,
    qdrant: QdrantClient,
    settings: IndexingSettings,
) -> IndexDocumentUseCase:
    return IndexDocumentUseCase(
        jobs=SqlAlchemyIndexJobWriteRepositorySync(session, tenant_id),
        documents=SqlAlchemyDocumentWriteRepositorySync(session, tenant_id),
        storage_read=MinioObjectStorageReader(minio),
        qdrant_write=QdrantVectorWriter(qdrant),
        llm=settings.llm,
        embedding=settings.embedding,
    )


@celery_app.task(
    name=_settings.index_document_task_name,
    bind=True,
    max_retries=_settings.index_document_max_retries,
)
def index_document_task(
    self,
    job_id: str,
    document_id: str,
    minio_key: str,
    filename: str,
    tenant_id: str = "default",
) -> dict:
    """Download PDF from MinIO, semantic chunk, upsert to Qdrant."""
    jid = uuid.UUID(job_id)
    did = uuid.UUID(document_id)
    logger.info(
        "index_document started job_id=%s document_id=%s tenant_id=%s",
        job_id,
        document_id,
        tenant_id,
    )
    session = SessionLocal()
    minio = MinioClient(_settings.minio)
    qdrant = QdrantClient(_settings.qdrant)

    try:
        use_case = _build_use_case(
            session,
            tenant_id,
            minio=minio,
            qdrant=qdrant,
            settings=_settings,
        )
        result = use_case.run(
            job_id=jid,
            document_id=did,
            minio_key=minio_key,
            filename=filename,
            tenant_id=tenant_id,
            mark_running=self.request.retries == 0,
        )
        logger.info(
            "index_document completed job_id=%s document_id=%s chunks=%s",
            job_id,
            result.document_id,
            result.chunk_count,
        )
        return result.to_celery_result()
    except Exception as exc:
        session.rollback()
        jobs = SqlAlchemyIndexJobWriteRepositorySync(session, tenant_id)
        terminal = self.request.retries >= self.max_retries
        jobs.update_status(
            jid,
            JobStatus.FAILED if terminal else JobStatus.RUNNING,
            error=str(exc) if terminal else f"Attempt {self.request.retries + 1} failed: {exc}",
        )
        if terminal:
            logger.exception("index_document failed job_id=%s", job_id)
            raise
        logger.warning(
            "index_document attempt failed job_id=%s retries=%s",
            job_id,
            self.request.retries + 1,
        )
        raise self.retry(exc=exc, countdown=_settings.index_document_retry_countdown) from exc
    finally:
        minio.close()
        qdrant.close()
        session.close()
