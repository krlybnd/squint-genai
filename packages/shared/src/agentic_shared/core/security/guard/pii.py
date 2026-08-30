from __future__ import annotations

import re
from dataclasses import dataclass, field

REDACTED = "[PII_REDACTED]"

_KIND_BY_PLACEHOLDER = {
    "[EMAIL_REDACTED]": "email",
    "[PHONE_REDACTED]": "telefon",
    "[IBAN_REDACTED]": "iban",
    "[CARD_REDACTED]": "bankkártya",
    "[IP_REDACTED]": "ip_cím",
    "[TAJ_REDACTED]": "taj",
    "[ID_REDACTED]": "személyi_azonosító",
    "[TAX_ID_REDACTED]": "adószám",
    "[DATE_REDACTED]": "dátum",
    "[PASSPORT_REDACTED]": "útlevél",
    REDACTED: "érzékeny_mező",
}

# GDPR-relevant identifiers and contact/financial/health data (HU + common intl).
_PII_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL_REDACTED]"),
    (
        re.compile(
            r"\b(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3}[\s-]?\d{2,4}[\s-]?\d{2,4}\b"
        ),
        "[PHONE_REDACTED]",
    ),
    (re.compile(r"\b\+36[\s/-]?\d{1,2}[\s/-]?\d{3}[\s/-]?\d{4}\b"), "[PHONE_REDACTED]"),
    (re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"), "[IBAN_REDACTED]"),
    (re.compile(r"\b(?:\d{4}[\s-]?){3}\d{4}\b"), "[CARD_REDACTED]"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[IP_REDACTED]"),
    (re.compile(r"\b\d{3}[\s-]?\d{3}[\s-]?\d{3}\b"), "[TAJ_REDACTED]"),
    (re.compile(r"\b\d{6}[\s-]?[A-Z]{2}\b"), "[ID_REDACTED]"),
    (re.compile(r"\b\d{8}[\s-]?\d{1}\b"), "[TAX_ID_REDACTED]"),
    (
        re.compile(r"\b(?:19|20)\d{2}[./-](?:0[1-9]|1[0-2])[./-](?:0[1-9]|[12]\d|3[01])\b"),
        "[DATE_REDACTED]",
    ),
    (
        re.compile(r"\b(?:0[1-9]|[12]\d|3[01])[./-](?:0[1-9]|1[0-2])[./-](?:19|20)\d{2}\b"),
        "[DATE_REDACTED]",
    ),
    (re.compile(r"\b[A-Z]{1,2}\d{6,8}\b"), "[PASSPORT_REDACTED]"),
)

_SENSITIVE_FIELD = re.compile(
    r"(?i)(név|vezetéknév|keresztnév|name|e-mail|email|telefon|phone|mobil|"
    r"cím|address|lakcím|születési\s+dátum|születés|taj|személyi|adószám|"
    r"iban|bankszámla|számlaszám|anyja\s+neve|taj\s+szám)\s*[:\-=]\s*[^\n,;]+"
)


@dataclass(frozen=True, slots=True)
class RedactionDetail:
    kind: str
    placeholder: str


@dataclass(frozen=True, slots=True)
class RedactionResult:
    text: str
    count: int
    details: list[RedactionDetail] = field(default_factory=list)


def _append_details(details: list[RedactionDetail], placeholder: str, n: int) -> None:
    if n <= 0:
        return
    kind = _KIND_BY_PLACEHOLDER.get(placeholder, "egyéb")
    for _ in range(n):
        details.append(RedactionDetail(kind=kind, placeholder=placeholder))


def redact_pii(text: str) -> RedactionResult:
    if not text:
        return RedactionResult("", 0, [])

    redacted = text
    count = 0
    details: list[RedactionDetail] = []
    for pattern, replacement in _PII_RULES:
        redacted, n = pattern.subn(replacement, redacted)
        count += n
        _append_details(details, replacement, n)

    def _field_repl(match: re.Match[str]) -> str:
        label = (match.group(1) or "mező").strip().lower()
        details.append(RedactionDetail(kind=label, placeholder=REDACTED))
        return f"{match.group(1)}: {REDACTED}"

    redacted, n = _SENSITIVE_FIELD.subn(_field_repl, redacted)
    count += n
    return RedactionResult(redacted, count, details)
