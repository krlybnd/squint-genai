import pytest
from dishka import Provider, Scope, make_async_container, provide

from agentic_shared.core.health.providers import make_resource_health_provider
from agentic_shared.core.health.service import ResourceHealthService


class _StubClient:
    def __init__(self, title: str) -> None:
        self._title = title

    @property
    def title(self) -> str:
        return self._title

    async def health_check(self) -> bool:
        return True


class _StubDatabaseClient(_StubClient):
    pass


class _StubChatClient(_StubClient):
    pass


class _StubClientsProvider(Provider):
    @provide(scope=Scope.APP)
    def database_client(self) -> _StubDatabaseClient:
        return _StubDatabaseClient("postgresql")

    @provide(scope=Scope.APP)
    def chat_client(self) -> _StubChatClient:
        return _StubChatClient("llm")


@pytest.mark.asyncio
async def test_make_resource_health_provider_wires_registered_clients() -> None:
    # Arrange
    container = make_async_container(
        _StubClientsProvider(),
        make_resource_health_provider(_StubDatabaseClient, _StubChatClient),
    )

    # Act
    async with container() as request_container:
        service = await request_container.get(ResourceHealthService)

    # Assert
    assert await service.readiness() == {"postgresql": True, "llm": True}


def test_make_resource_health_provider_empty_returns_no_dependencies() -> None:
    # Arrange
    provider = make_resource_health_provider()

    # Act
    resource_health_service = provider.resource_health_service

    # Assert
    assert isinstance(resource_health_service, object)


def test_make_resource_health_provider_registers_two_dependencies() -> None:
    # Arrange / Act
    provider = make_resource_health_provider(_StubDatabaseClient, _StubChatClient)

    # Assert
    assert provider.__class__.__name__ == "ConfiguredResourceHealthProvider"
    assert hasattr(provider, "resource_health_service")
