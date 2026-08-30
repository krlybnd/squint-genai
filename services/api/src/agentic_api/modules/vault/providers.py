from agentic_shared.domains.pii_vault.protocols import PiiVaultReadRepository
from dishka import Provider, Scope, provide

from agentic_api.modules.vault.service import VaultApiService


class VaultApiProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def vault_api_service(
        self, pii_vault_read_repository: PiiVaultReadRepository
    ) -> VaultApiService:
        return VaultApiService(pii_vault_read_repository)


__all__ = ["VaultApiProvider"]
