"""Investigation eval corpus fixtures — all fictional Kamu* entities."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Sync with resources/eval/README.md embedded PII table.
INVESTIGATION_PII_ENTITIES: tuple[str, ...] = (
    "Esther Szabo",
    "99999999-9-99",
    "eszabo.eval-fixture@example.invalid",
    "+36 99 000 0001",
    "HU68 KAMU 0001 2345 6789 0123 4567",
    "9999 Tesztváros, Kamu utca 47.",
    "Dr. Levente Varga",
)

CROSS_DOC_FINDING_IDS: tuple[str, ...] = (
    "F-01",
    "F-02",
    "F-03",
    "F-04",
    "F-05",
    "F-06",
    "F-07",
)

# Patterns that must NOT appear — real bank/company leakage guard for corpus CI.
FORBIDDEN_REAL_ENTITY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bOTP\b", re.IGNORECASE),
    re.compile(r"\bHoldex\b", re.IGNORECASE),
    re.compile(r"\bNovaBridge\b", re.IGNORECASE),
    re.compile(r"\bTechLine\b", re.IGNORECASE),
    re.compile(r"\b11773377\b"),
    re.compile(r"\b84592163\b"),
    re.compile(r"\bBudapest\b", re.IGNORECASE),
    re.compile(r"Váci\s+út", re.IGNORECASE),
)

REQUIRED_CORPUS_MARKERS: tuple[str, ...] = (
    "SYNTHETIC TEST MATERIAL",
    "Kamuhold Beruházási Zrt.",
    "Kamuhold Építő Kft.",
    "99990001-00000001",
)

BANNED_SUBSTRINGS_FIXTURES: tuple[str, ...] = (
    "squint-e2e-banned",
    "motherfucker",
    "fuck you",
)


@dataclass(frozen=True, slots=True)
class PiiScanResult:
    entity: str
    found: bool


def scan_plaintext_pii(
    text: str,
    entities: tuple[str, ...] = INVESTIGATION_PII_ENTITIES,
) -> list[PiiScanResult]:
    return [PiiScanResult(entity=entity, found=entity in text) for entity in entities]


def count_pii_leaks(text: str) -> int:
    return sum(1 for item in scan_plaintext_pii(text) if item.found)


def find_forbidden_real_entities(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in FORBIDDEN_REAL_ENTITY_PATTERNS:
        if pattern.search(text):
            hits.append(pattern.pattern)
    return hits
