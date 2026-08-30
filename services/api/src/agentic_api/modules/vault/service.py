import logging

from agentic_shared.crosscut.auth.context import AuthContext
from agentic_shared.domains.pii_vault.protocols import PiiVaultReadRepository

from agentic_api.modules.vault.schemas import DetokenizeResponse

logger = logging.getLogger(__name__)


class VaultApiService:
    def __init__(self, vault: PiiVaultReadRepository) -> None:
        self._vault = vault

    async def detokenize(
        self,
        tokens: list[str],
        *,
        auth: AuthContext,
        tenant_id: str,
    ) -> DetokenizeResponse:
        values = await self._vault.resolve_tokens(tokens)
        logger.info(
            "vault detokenize user_id=%s tenant_id=%s requested=%d resolved=%d",
            auth.user_id,
            tenant_id,
            len(tokens),
            len(values),
        )
        return DetokenizeResponse(
            values={token: secret.get_secret_value() for token, secret in values.items()},
        )


__all__ = ["VaultApiService"]
