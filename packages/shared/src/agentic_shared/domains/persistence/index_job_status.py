from datetime import UTC, datetime

from agentic_shared.domains.persistence.entities import IndexJob, JobStatus


def apply_index_job_status(
    job: IndexJob,
    status: JobStatus,
    *,
    error: str | None = None,
) -> None:
    job.status = status
    job.error_message = error
    if status in (JobStatus.COMPLETED, JobStatus.FAILED):
        job.completed_at = datetime.now(UTC)
