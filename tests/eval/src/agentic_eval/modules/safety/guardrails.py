"""Load guardrail eval cases and simulate BanSubstrings matching (offline)."""

from __future__ import annotations

import json
from pathlib import Path

from agentic_eval.modules.safety.fixtures import BANNED_SUBSTRINGS_FIXTURES
from agentic_eval.modules.safety.investigation import GUARDRAILS_CASES_PATH
from agentic_eval.modules.safety.metrics import GuardrailEvalCase, GuardrailOutcome


def load_guardrail_cases(path: Path | None = None) -> list[GuardrailEvalCase]:
    dataset = path if path is not None else GUARDRAILS_CASES_PATH
    raw = json.loads(dataset.read_text(encoding="utf-8"))
    return [GuardrailEvalCase.model_validate(item) for item in raw]


def ban_substrings_would_block(
    text: str,
    substrings: tuple[str, ...] = BANNED_SUBSTRINGS_FIXTURES,
) -> bool:
    lowered = text.lower()
    return any(token.lower() in lowered for token in substrings)


def simulate_ban_substrings_outcomes(
    cases: list[GuardrailEvalCase] | None = None,
) -> list[GuardrailOutcome]:
    items = cases if cases is not None else load_guardrail_cases()
    ban_cases = [item for item in items if item.category != "overdefense"]
    return [
        GuardrailOutcome(
            case_id=item.id,
            category=item.category,
            blocked=ban_substrings_would_block(item.input),
        )
        for item in ban_cases
    ]


def outcomes_match_expectations(
    cases: list[GuardrailEvalCase],
    outcomes: list[GuardrailOutcome],
) -> list[str]:
    by_id = {item.case_id: item for item in outcomes}
    failures: list[str] = []
    for case in cases:
        outcome = by_id.get(case.id)
        if outcome is None:
            failures.append(f"missing outcome for {case.id}")
            continue
        if outcome.blocked != case.expected_blocked:
            failures.append(
                f"{case.id}: expected blocked={case.expected_blocked}, "
                f"got blocked={outcome.blocked}"
            )
    return failures
