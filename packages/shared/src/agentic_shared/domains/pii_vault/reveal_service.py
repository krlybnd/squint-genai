"""Replace vault tokens with decrypted plaintext for authorized callers."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any

from agentic_shared.domains.pii_vault.protocols import PiiVaultReadRepository

VAULT_TOKEN_PATTERN = re.compile(r"<[A-Z0-9_]+_[A-F0-9]{8}>")
_TOKEN_PREFIX = re.compile(r"^<[A-Z0-9_]*(_[A-F0-9]{0,8})?$")
_MARKED_SPAN_RE = re.compile(r"\[\[vault:<[A-Z0-9_]+_[A-F0-9]{8}>\]\][\s\S]*?\[\[/vault\]\]")
_MAX_TOKEN_LEN = 80
_MIN_PLAINTEXT_LEN = 3
VAULT_MARK_OPEN = "[[vault:"
VAULT_MARK_CLOSE = "[[/vault]]"


def format_revealed_vault_span(token: str, plaintext: str) -> str:
    """Wrap revealed plaintext so the UI can color it and show the vault token."""
    safe = plaintext.replace(VAULT_MARK_CLOSE, "")
    return f"{VAULT_MARK_OPEN}{token}]]{safe}{VAULT_MARK_CLOSE}"


def collect_vault_tokens(*values: object) -> list[str]:
    """Find vault tokens in any nested retrieve/generate payload."""
    parts: list[str] = []

    def walk(value: object) -> None:
        if isinstance(value, str):
            if "<" in value:
                parts.append(value)
            return
        if isinstance(value, Mapping):
            for item in value.values():
                walk(item)
            return
        if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
            for item in value:
                walk(item)

    for value in values:
        walk(value)
    return sorted(set(VAULT_TOKEN_PATTERN.findall("\n".join(parts))))


def mark_known_vault_values(text: str, values: Mapping[str, str]) -> str:
    """Wrap vault plaintext the model copied without emitting the token."""
    pairs = [
        (token, value)
        for token, value in values.items()
        if value and len(_fold(value)) >= _MIN_PLAINTEXT_LEN
    ]
    pairs.sort(key=lambda item: len(_fold(item[1])), reverse=True)
    marked = text
    for token, value in pairs:
        marked = _replace_outside_marks(marked, token, value)
    return marked


def _fold(text: str) -> str:
    stripped = "".join(
        char for char in unicodedata.normalize("NFD", text) if unicodedata.category(char) != "Mn"
    )
    return stripped.casefold()


def _fold_index_map(text: str) -> list[int]:
    mapping: list[int] = []
    for index, char in enumerate(text):
        folded = _fold(char)
        mapping.extend([index] * max(len(folded), 0))
    mapping.append(len(text))
    return mapping


def _find_folded_spans(haystack: str, needle: str) -> list[tuple[int, int]]:
    folded_hay = _fold(haystack)
    folded_needle = _fold(needle)
    if not folded_needle:
        return []
    mapping = _fold_index_map(haystack)
    spans: list[tuple[int, int]] = []
    start = 0
    while True:
        index = folded_hay.find(folded_needle, start)
        if index == -1:
            break
        spans.append((mapping[index], mapping[index + len(folded_needle)]))
        start = index + len(folded_needle)
    return spans


def _replace_outside_marks(text: str, token: str, plaintext: str) -> str:
    parts: list[str] = []
    last = 0
    for match in _MARKED_SPAN_RE.finditer(text):
        parts.append(_replace_plain_segment(text[last : match.start()], token, plaintext))
        parts.append(match.group(0))
        last = match.end()
    parts.append(_replace_plain_segment(text[last:], token, plaintext))
    return "".join(parts)


def _replace_plain_segment(segment: str, token: str, plaintext: str) -> str:
    if not segment or not plaintext:
        return segment
    spans = _find_folded_spans(segment, plaintext)
    if not spans:
        return segment
    pieces: list[str] = []
    cursor = 0
    for start, end in spans:
        pieces.append(segment[cursor:start])
        pieces.append(format_revealed_vault_span(token, segment[start:end]))
        cursor = end
    pieces.append(segment[cursor:])
    return "".join(pieces)


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

    async def reveal_text(
        self,
        text: str,
        *,
        marked: bool = False,
        extra_tokens: Sequence[str] = (),
    ) -> str:
        tokens = sorted(
            set(self.find_tokens(text))
            | {token for token in extra_tokens if VAULT_TOKEN_PATTERN.fullmatch(token)}
        )
        if not tokens:
            return text
        values = await self._vault.resolve_tokens(tokens)
        revealed = text
        for token, secret in values.items():
            plaintext = secret.get_secret_value()
            replacement = format_revealed_vault_span(token, plaintext) if marked else plaintext
            revealed = revealed.replace(token, replacement)
        if marked:
            mapping = {token: secret.get_secret_value() for token, secret in values.items()}
            revealed = mark_known_vault_values(revealed, mapping)
        return revealed

    async def reveal_mapping(self, tokens: Sequence[str]) -> dict[str, str]:
        values = await self._vault.resolve_tokens(tokens)
        return {token: secret.get_secret_value() for token, secret in values.items()}

    async def reveal_citations(
        self, citations: Sequence[Mapping[str, Any]], *, marked: bool = False
    ) -> list[dict[str, Any]]:
        revealed: list[dict[str, Any]] = []
        for citation in citations:
            item = dict(citation)
            for field in ("text", "excerpt", "selected_text"):
                raw = item.get(field)
                if isinstance(raw, str) and raw:
                    item[field] = await self.reveal_text(raw, marked=marked)
            revealed.append(item)
        return revealed


class StreamingVaultReveal:
    """Incremental detokenizer for SSE token chunks (handles split vault tokens)."""

    def __init__(self, vault: VaultRevealService, *, marked: bool = False) -> None:
        self._vault = vault
        self._marked = marked
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
        plaintext = mapping.get(token)
        if plaintext is None:
            self._cache[token] = token
            return token
        rendered = format_revealed_vault_span(token, plaintext) if self._marked else plaintext
        self._cache[token] = rendered
        return rendered


__all__ = [
    "StreamingVaultReveal",
    "VAULT_MARK_CLOSE",
    "VAULT_MARK_OPEN",
    "VAULT_TOKEN_PATTERN",
    "VaultRevealService",
    "collect_vault_tokens",
    "format_revealed_vault_span",
    "mark_known_vault_values",
]
