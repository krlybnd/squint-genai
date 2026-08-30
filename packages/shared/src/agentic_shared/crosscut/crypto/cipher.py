"""Symmetric encryption port + Fernet implementation."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cryptography.fernet import Fernet, InvalidToken

from agentic_shared.core.settings.secrets import SecuredStr
from agentic_shared.crosscut.crypto.settings import CryptoSettings


def _unwrap_secret(value: str | SecuredStr) -> str:
    if isinstance(value, SecuredStr):
        return value.get_secret_value()
    return value


@runtime_checkable
class Cipher(Protocol):
    def encrypt(self, plaintext: str | SecuredStr) -> str: ...

    def decrypt(self, ciphertext: str) -> SecuredStr: ...


class FernetCipher:
    """AES-128-CBC + HMAC via cryptography.Fernet."""

    def __init__(self, settings: CryptoSettings) -> None:
        self._fernet = Fernet(settings.fernet_key)

    def encrypt(self, plaintext: str | SecuredStr) -> str:
        token = self._fernet.encrypt(_unwrap_secret(plaintext).encode("utf-8"))
        return token.decode("ascii")

    def decrypt(self, ciphertext: str) -> SecuredStr:
        try:
            data = self._fernet.decrypt(ciphertext.encode("ascii"))
        except InvalidToken as exc:
            raise ValueError("vault ciphertext decrypt failed") from exc
        return SecuredStr(data.decode("utf-8"))


__all__ = ["Cipher", "FernetCipher"]
