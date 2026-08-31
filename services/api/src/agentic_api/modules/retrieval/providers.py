from agentic_shared.domains.pii_vault.reveal_service import VaultRevealService
from agentic_shared.domains.pii_vault.settings import PiiVaultSettings
from agentic_shared.domains.retrieval.protocols import AsyncRetrievalReader
from agentic_shared.domains.retrieval.providers import AsyncRetrievalProvider
from dishka import Scope, provide

from agentic_api.modules.retrieval.service import RetrievalApiService
from agentic_api.settings import ApiSettings


class RetrievalProvider(AsyncRetrievalProvider):
    def __init__(self, settings: ApiSettings) -> None:
        super().__init__(
            settings.llm,
            settings.embedding,
        )
        self._settings = settings

    @provide(scope=Scope.REQUEST)
    def retrieval_api(
        self,
        async_retrieval_reader: AsyncRetrievalReader,
        vault_reveal: VaultRevealService,
        pii_vault: PiiVaultSettings,
    ) -> RetrievalApiService:
        return RetrievalApiService(
            async_retrieval_reader,
            self._settings,
            vault_reveal=vault_reveal,
            pii_vault=pii_vault,
        )
