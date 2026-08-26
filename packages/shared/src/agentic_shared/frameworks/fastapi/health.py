from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter
from pydantic import BaseModel

from agentic_shared.core.health.service import ResourceHealthService

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready")
@inject
async def ready(
    resource_health_service: FromDishka[ResourceHealthService],
) -> dict[str, str | bool]:
    checks = await resource_health_service.readiness()
    status = "ready" if checks and all(checks.values()) else "degraded"
    return {"status": status, **checks}
