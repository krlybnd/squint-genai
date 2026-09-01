"""Deterministic DeepEval ``BaseMetric`` extensions for generation goldens."""

from __future__ import annotations

import re
from collections.abc import Sequence

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase, SingleTurnParams

_GUARD = (
    "rejected by the security check",
    "prompt injection",
    "sicherheitsprüfung abgelehnt",
    "biztonsági ellenőrzésen elutasításra",
)
_FACT = re.compile(
    r"\d{2,}[-/]\d+|ART-\d+|KAH-[A-Z0-9/-]+|HUF\s*[\d,.]+|HU\d{2}|IBAN",
    re.IGNORECASE,
)


def guard_block(answer: str) -> bool:
    text = answer.lower()
    return any(marker in text for marker in _GUARD)


def clean_refusal(answer: str, markers: Sequence[str], question: str) -> bool:
    text = answer.lower()
    if guard_block(answer) or not any(marker in text for marker in markers):
        return False
    q = question.lower()
    return all(token.lower() in q for token in _FACT.findall(answer))


class RequiredPhrasesMetric(BaseMetric):
    _required_params: list[SingleTurnParams] = [SingleTurnParams.ACTUAL_OUTPUT]

    def __init__(self, threshold: float = 1.0) -> None:
        self.threshold = threshold
        self.async_mode = False
        self.verbose_mode = False

    def measure(self, test_case: LLMTestCase, *args: object, **kwargs: object) -> float:
        self.skipped = False
        if "abstention" in list(test_case.tags or []):
            self.skipped = True
            self.score = 1.0
            self.reason = "Abstention golden has no required phrases."
            self.success = True
            return self.score
        phrases = (test_case.metadata or {}).get("required_phrases") or []
        text = (test_case.actual_output or "").lower()
        missing = [p for p in phrases if str(p).lower() not in text]
        self.score = 0.0 if missing else 1.0
        self.reason = "ok" if not missing else f"Missing: {', '.join(map(str, missing))}"
        self.success = self.is_successful()
        return self.score

    async def a_measure(self, test_case: LLMTestCase, *args: object, **kwargs: object) -> float:
        return self.measure(test_case, *args, **kwargs)

    @property
    def __name__(self) -> str:
        return "Required Phrases"


class AbstentionMetric(BaseMetric):
    _required_params: list[SingleTurnParams] = [
        SingleTurnParams.INPUT,
        SingleTurnParams.ACTUAL_OUTPUT,
    ]

    def __init__(self, markers: Sequence[str], threshold: float = 1.0) -> None:
        self.markers = tuple(markers)
        self.threshold = threshold
        self.async_mode = False
        self.verbose_mode = False

    def measure(self, test_case: LLMTestCase, *args: object, **kwargs: object) -> float:
        self.skipped = False
        refused = clean_refusal(test_case.actual_output or "", self.markers, test_case.input)
        if "abstention" in list(test_case.tags or []):
            self.score = 1.0 if refused else 0.0
            self.reason = "Clean refusal as expected." if refused else "Expected a clean refusal."
        else:
            self.score = 0.0 if refused else 1.0
            self.reason = "False abstention." if refused else "Labeled question was answered."
        self.success = self.is_successful()
        return self.score

    async def a_measure(self, test_case: LLMTestCase, *args: object, **kwargs: object) -> float:
        return self.measure(test_case, *args, **kwargs)

    @property
    def __name__(self) -> str:
        return "Abstention"
