"""Replace vault tokens with decrypted plaintext for authorized callers."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from agentic_shared.domains.pii_vault.protocols import PiiVaultReadRepository

VAULT_TOKEN_PATTERN = re.compile(r"<[A-Z0-9_]+_[A-F0-9]{8}>")
_TOKEN_PREFIX = re.compile(r"^<[A-Z0-9_]*(_[A-F0-9]{0,8})?$")
_MAX_TOKEN_LEN = 80


def _is_token_prefix(text: str) -> bool:
    if not text.startswith("<"):
        return False
    if VAULT_TOKEN_PATTERN.match(text):
        return False
    return bool(_TOKEN_PREFIX.match(text))


class VaultRevealService:
    def __init__(self, vault: PiiVaultReadRepository) -> None:
        self._vault = vault

    @staticmethod
    def find_tokens(text: str) -> list[str]:
        return sorted(set(VAULT_TOKEN_PATTERN.findall(text)))

    async def reveal_text(self, text: str) -> str:
        tokens = self.find_tokens(text)
        if not tokens:
            return text
        values = await self._vault.resolve_tokens(tokens)
        revealed = text
        for token, secret in values.items():
            revealed = revealed.replace(token, secret.get_secret_value())
        return revealed

    async def reveal_mapping(self, tokens: Sequence[str]) -> dict[str, str]:
        values = await self._vault.resolve_tokens(tokens)
        return {token: secret.get_secret_value() for token, secret in values.items()}

    async def reveal_citations(
        self, citations: Sequence[Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        revealed: list[dict[str, Any]] = []
        for citation in citations:
            item = dict(citation)
            for field in ("text", "excerpt", "selected_text"):
                raw = item.get(field)
                if isinstance(raw, str) and raw:
                    item[field] = await self.reveal_text(raw)
            revealed.append(item)
        return revealed


class StreamingVaultReveal:
    """Incremental detokenizer for SSE token chunks (handles split vault tokens)."""

    def __init__(self, vault: VaultRevealService) -> None:
        self._vault = vault
        self._buffer = ""
        self._cache: dict[str, str] = {}

    async def feed(self, chunk: str) -> str:
        self._buffer += chunk
        return await self._drain(safe_only=True)

    async def flush(self) -> str:
        revealed = await self._drain(safe_only=False)
        if self._buffer:
            revealed += self._buffer
            self._buffer = ""
        return revealed

    async def _drain(self, *, safe_only: bool) -> str:
        output_parts: list[str] = []
        while self._buffer:
            lt = self._buffer.find("<")
            if lt == -1:
                output_parts.append(self._buffer)
                self._buffer = ""
                break

            if lt > 0:
                output_parts.append(self._buffer[:lt])
                self._buffer = self._buffer[lt:]

            match = VAULT_TOKEN_PATTERN.match(self._buffer)
            if match:
                token = match.group(0)
                output_parts.append(await self._resolve(token))
                self._buffer = self._buffer[len(token) :]
                continue

            if safe_only and _is_token_prefix(self._buffer):
                if len(self._buffer) > _MAX_TOKEN_LEN:
                    output_parts.append("<")
                    self._buffer = self._buffer[1:]
                    continue
                break

            output_parts.append("<")
            self._buffer = self._buffer[1:]

        return "".join(output_parts)

    async def _resolve(self, token: str) -> str:
        cached = self._cache.get(token)
        if cached is not None:
            return cached
        mapping = await self._vault.reveal_mapping([token])
        plaintext = mapping.get(token, token)
        self._cache[token] = plaintext
        return plaintext


__all__ = ["StreamingVaultReveal", "VAULT_TOKEN_PATTERN", "VaultRevealService"]
