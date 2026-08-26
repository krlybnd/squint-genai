SUPPORTED_LOCALES = frozenset({"en", "hu", "de"})
DEFAULT_LOCALE = "en"


def resolve_locale(accept_language: str | None) -> str:
    """Parse Accept-Language header (e.g. ``hu-HU,hu;q=0.9,en;q=0.8``)."""
    if not accept_language:
        return DEFAULT_LOCALE
    for part in accept_language.split(","):
        token = part.split(";")[0].strip().lower()
        if not token:
            continue
        primary = token.split("-")[0]
        if primary in SUPPORTED_LOCALES:
            return primary
    return DEFAULT_LOCALE
