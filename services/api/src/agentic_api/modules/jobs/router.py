from uuid import UUID

from agentic_shared.core.auth.context import AuthContext
from agentic_shared.core.auth.roles import AppRole
from agentic_shared.core.auth.settings import AuthSettings
from agentic_shared.core.i18n import resolve_locale, t_stored
from agentic_shared.frameworks.fastapi.auth.dependencies import require_roles
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException, Request, status

from agentic_api.modules.jobs.schemas import IndexAllResponse, JobOut
from agentic_api.modules.jobs.service import JobService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/index", response_model=IndexAllResponse, status_code=status.HTTP_202_ACCEPTED)
@inject
async def trigger_reindex_all(
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    job_service: FromDishka[JobService],
) -> IndexAllResponse:
    require_roles(auth, auth_settings, AppRole.ADMIN)
    job_ids = await job_service.enqueue_reindex_all()
    return IndexAllResponse(
        job_ids=job_ids,
        message=f"Enqueued {len(job_ids)} indexing job(s)",
    )


@router.get("/jobs/{job_id}", response_model=JobOut)
@inject
async def get_job(
    job_id: UUID,
    request: Request,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    job_service: FromDishka[JobService],
) -> JobOut:
    require_roles(auth, auth_settings, AppRole.READ)
    job = await job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    locale = resolve_locale(request.headers.get("accept-language"))
    return JobOut(
        id=job.id,
        document_id=job.document_id,
        celery_task_id=job.celery_task_id,
        status=job.status.value,
        error_message=t_stored(job.error_message, locale),
        created_at=job.created_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )
