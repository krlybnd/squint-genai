"""Tenant-scoped vault detokenize for live generation eval (mirrors chat SSE reveal)."""

from __future__ import annotations

from pathlib import Path

from agentic_shared.crosscut.crypto.cipher import FernetCipher
from agentic_shared.crosscut.crypto.settings import CryptoSettings
from agentic_shared.domains.persistence.repositories.async_.pii_vault import (
    SqlAlchemyPiiVaultReadRepository,
)
from agentic_shared.domains.pii_vault.reveal_service import VaultRevealService
from agentic_shared.domains.pii_vault.settings import PiiVaultSettings
from agentic_shared.infrastructure.sql.postgres.settings import DatabaseSettings
from dotenv import dotenv_values
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from agentic_eval.modules.generation.types import GenerationResult


class EvalVaultReveal:
    """Resolve vault tokens in graph answers/contexts for the eval tenant."""

    def __init__(self, *, tenant_id: str, env_file: Path | None) -> None:
        vault = PiiVaultSettings(_env_file=env_file)
        self._enabled = vault.enabled
        self._tenant_id = tenant_id
        self._session_factory = None
        self._engine = None
        if not self._enabled:
            return
        crypto = CryptoSettings(_env_file=env_file)
        database = DatabaseSettings(_env_file=env_file)
        database_url = database.database_url
        if env_file is not None and env_file.is_file():
            file_url = dotenv_values(env_file).get("DATABASE_URL")
            if isinstance(file_url, str) and file_url.strip():
                database_url = file_url.strip()
        self._cipher = FernetCipher(crypto)
        self._engine: AsyncEngine = create_async_engine(database_url, echo=False)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def reveal_text(self, text: str) -> str:
        if not self._enabled or self._session_factory is None:
            return text
        async with self._session_factory() as session:
            repo = SqlAlchemyPiiVaultReadRepository(session, self._tenant_id, self._cipher)
            return await VaultRevealService(repo).reveal_text(text)

    async def reveal_result(self, result: GenerationResult) -> GenerationResult:
        if not self._enabled:
            return result
        answer = await self.reveal_text(result.answer)
        contexts = [await self.reveal_text(context) for context in result.contexts]
        return GenerationResult(answer=answer, contexts=contexts)

    async def aclose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()


__all__ = ["EvalVaultReveal"]
