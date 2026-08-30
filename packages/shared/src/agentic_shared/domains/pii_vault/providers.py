from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from agentic_shared.crosscut.auth.context import AuthContext
from agentic_shared.crosscut.auth.tenant import resolve_tenant_id
from agentic_shared.crosscut.crypto.cipher import FernetCipher
from agentic_shared.crosscut.crypto.settings import CryptoSettings
from agentic_shared.domains.persistence.repositories.async_.pii_vault import (
    SqlAlchemyPiiVaultReadRepository,
)
from agentic_shared.domains.pii_vault.protocols import PiiVaultReadRepository
from agentic_shared.domains.pii_vault.query_service import QueryPiiTokenizationService
from agentic_shared.domains.pii_vault.reveal_service import VaultRevealService
from agentic_shared.domains.pii_vault.settings import PiiVaultSettings
from agentic_shared.domains.pii_vault.tokenizer import PiiTokenizer
from agentic_shared.integrations.litellm.analyzer.protocols import Analyzer


class PiiVaultProvider(Provider):
    def __init__(self, crypto: CryptoSettings, vault_settings: PiiVaultSettings) -> None:
        super().__init__()
        self._crypto = crypto
        self._vault_settings = vault_settings
        self._cipher = FernetCipher(crypto)
        self._tokenizer = PiiTokenizer(token_salt=crypto.token_salt)

    @provide(scope=Scope.APP)
    def pii_vault_settings(self) -> PiiVaultSettings:
        return self._vault_settings

    @provide(scope=Scope.APP)
    def pii_tokenizer(self) -> PiiTokenizer:
        return self._tokenizer

    @provide(scope=Scope.REQUEST)
    def pii_vault_read_repository(
        self,
        session: AsyncSession,
        auth: AuthContext,
    ) -> PiiVaultReadRepository:
        return SqlAlchemyPiiVaultReadRepository(
            session,
            resolve_tenant_id(auth),
            self._cipher,
        )

    @provide(scope=Scope.APP)
    def query_pii_tokenization(
        self,
        analyzer: Analyzer,
    ) -> QueryPiiTokenizationService:
        return QueryPiiTokenizationService(
            analyzer=analyzer,
            tokenizer=self._tokenizer,
            settings=self._vault_settings,
        )

    @provide(scope=Scope.REQUEST)
    async def vault_reveal_service(
        self,
        pii_vault_read_repository: PiiVaultReadRepository,
    ) -> AsyncIterator[VaultRevealService]:
        yield VaultRevealService(pii_vault_read_repository)


__all__ = ["PiiVaultProvider"]
