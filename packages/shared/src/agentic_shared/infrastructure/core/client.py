from agentic_shared.core.resources.client import (
    BaseResourceClient as BaseInfraClient,
)
from agentic_shared.core.resources.client import (
    ResourceClient as InfraClient,
)
from agentic_shared.core.resources.client import (
    open_resource as open_client,
)

__all__ = ["BaseInfraClient", "InfraClient", "open_client"]
