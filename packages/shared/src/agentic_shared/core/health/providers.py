import inspect
import re
from collections.abc import Callable
from typing import cast

from dishka import Provider, Scope, provide

from agentic_shared.core.health.protocols import ResourceHealthCheckable
from agentic_shared.core.health.service import ResourceHealthService


def _param_name(resource_type: type) -> str:
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", resource_type.__name__).lower()


def _resource_health_service_method(
    resource_types: tuple[type, ...],
) -> Callable[..., ResourceHealthService]:
    """Build a typed provider method without runtime code generation."""
    param_names = [_param_name(resource_type) for resource_type in resource_types]

    def resource_health_service(self, **clients: object) -> ResourceHealthService:
        resources = cast(
            list[ResourceHealthCheckable],
            [clients[name] for name in param_names],
        )
        return ResourceHealthService(resources)

    annotations: dict[str, object] = {
        name: resource_type for name, resource_type in zip(param_names, resource_types, strict=True)
    }
    annotations["return"] = ResourceHealthService
    resource_health_service.__annotations__ = annotations

    parameters = [
        inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        *(
            inspect.Parameter(
                name,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=resource_type,
            )
            for name, resource_type in zip(param_names, resource_types, strict=True)
        ),
    ]
    resource_health_service.__signature__ = inspect.Signature(  # type: ignore[attr-defined]
        parameters,
        return_annotation=ResourceHealthService,
    )
    return resource_health_service


def make_resource_health_provider(*resource_types: type) -> Provider:
    """Build a Dishka provider that wires only the registered health-checkable resources."""
    if not resource_types:

        class EmptyResourceHealthProvider(Provider):
            @provide(scope=Scope.APP)
            def resource_health_service(self) -> ResourceHealthService:
                return ResourceHealthService([])

        return EmptyResourceHealthProvider()

    resource_health_service = _resource_health_service_method(resource_types)
    provided = provide(scope=Scope.APP)(
        cast(Callable[..., ResourceHealthService], resource_health_service)
    )

    class ConfiguredResourceHealthProvider(Provider):
        resource_health_service = provided

    return ConfiguredResourceHealthProvider()
