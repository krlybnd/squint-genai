"""Secret-bearing string for settings — repr/print hides the value."""

from pydantic import SecretStr

# Project alias: use on API keys, passwords, client secrets.
SecuredStr = SecretStr

__all__ = ["SecuredStr"]
