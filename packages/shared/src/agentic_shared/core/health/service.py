import logging

from agentic_shared.core.health.protocols import ResourceHealthCheckable

logger = logging.getLogger(__name__)


class ResourceHealthService:
    def __init__(self, resources: list[ResourceHealthCheckable]) -> None:
        self._resources = resources

    async def readiness(self) -> dict[str, bool]:
        results: dict[str, bool] = {}
        for resource in self._resources:
            try:
                healthy = await resource.health_check()
            except Exception:
                logger.warning(
                    "health check failed resource=%s",
                    resource.title,
                    exc_info=True,
                )
                healthy = False
            if not healthy:
                logger.debug("health check unhealthy resource=%s", resource.title)
            results[resource.title] = healthy
        return results
