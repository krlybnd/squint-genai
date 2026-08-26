import pytest

from agentic_shared.core.health.service import ResourceHealthService


class _StubClient:
    def __init__(self, title: str, healthy: bool, *, raises: bool = False) -> None:
        self._title = title
        self._healthy = healthy
        self._raises = raises

    @property
    def title(self) -> str:
        return self._title

    async def health_check(self) -> bool:
        if self._raises:
            raise RuntimeError("boom")
        return self._healthy


@pytest.mark.asyncio
async def test_resource_health_service_collects_client_results() -> None:
    # Arrange
    service = ResourceHealthService(
        [
            _StubClient("postgresql", True),
            _StubClient("redis", False),
        ]
    )

    # Act / Assert
    assert await service.readiness() == {"postgresql": True, "redis": False}


@pytest.mark.asyncio
async def test_resource_health_service_marks_failed_checks_false() -> None:
    # Arrange
    service = ResourceHealthService([_StubClient("qdrant", True, raises=True)])

    # Act / Assert
    assert await service.readiness() == {"qdrant": False}
