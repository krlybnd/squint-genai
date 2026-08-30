from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from agentic_shared.crosscut.i18n.locale import DEFAULT_LOCALE

LOCALE_LANGUAGE: dict[str, str] = {
    "en": "English",
    "hu": "Hungarian",
    "de": "German",
}


def _locales_dir() -> Path:
    """Checkout ``<repo>/locales/messages``, else wheel force-include."""
    here = Path(__file__).resolve()
    # crosscut/i18n → …/packages/shared/src/agentic_shared/crosscut/i18n → repo root
    candidates = (
        here.parents[6] / "locales" / "messages",
        here.parents[4] / "locales" / "messages",  # packages/shared/locales (symlink)
        here.parents[2] / "locales" / "messages",  # installed wheel
    )
    for path in candidates:
        if path.is_dir() and any(path.glob("*.json")):
            return path
    raise FileNotFoundError(
        "locale JSON not found under <repo>/locales/messages or agentic_shared/locales/messages"
    )


def _flatten_messages(node: dict[str, Any], prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in node.items():
        full = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            out.update(_flatten_messages(value, full))
        else:
            out[str(full)] = str(value)
    return out


@lru_cache(maxsize=1)
def _load_messages() -> dict[str, dict[str, str]]:
    by_locale: dict[str, dict[str, str]] = {}
    locales_dir = _locales_dir()
    for path in sorted(locales_dir.glob("*.json")):
        locale = path.stem
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"Locale file {path} must contain a JSON object")
        by_locale[locale] = _flatten_messages(data)
    if DEFAULT_LOCALE not in by_locale:
        default_path = locales_dir / f"{DEFAULT_LOCALE}.json"
        raise FileNotFoundError(f"Missing default locale JSON: {default_path}")
    return by_locale


_PLACEHOLDER = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def t(key: str, locale: str = DEFAULT_LOCALE, **kwargs: object) -> str:
    messages = _load_messages()
    loc = locale if locale in messages else DEFAULT_LOCALE
    template = messages[loc].get(key) or messages[DEFAULT_LOCALE].get(key, key)
    if not kwargs:
        return template

    def _replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in kwargs:
            return str(kwargs[name])
        return match.group(0)

    return _PLACEHOLDER.sub(_replace, template)


def t_stored(message: str | None, locale: str = DEFAULT_LOCALE, **kwargs: object) -> str | None:
    """Translate persisted i18n keys; pass through free-text errors from workers."""
    if message is None:
        return None
    catalog = _load_messages().get(DEFAULT_LOCALE, {})
    if message not in catalog:
        return message
    return t(message, locale, **kwargs)
