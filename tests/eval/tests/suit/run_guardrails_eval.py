"""Live llm-guard HTTP eval — attack block rate / benign pass rate / balanced accuracy."""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime

from agentic_shared.integrations.litellm.guard.client import GuardClient
from agentic_shared.integrations.litellm.guard.settings import GuardSettings

from agentic_eval.modules.safety.guardrails import load_guardrail_cases
from agentic_eval.modules.safety.metrics import GuardrailOutcome, aggregate_guardrail_scores
from agentic_eval.profiles import EvalProfile, get_profile
from agentic_eval.settings import EvalMode
from suit.settings import eval_env_file, load_suit_settings


async def _run_live_guardrails(profile_name: EvalProfile) -> int:
    profile = get_profile(profile_name)
    cases = load_guardrail_cases(profile.guardrails_cases_path)
    settings = GuardSettings()
    client = GuardClient(settings)
    try:
        if not await client.health_check():
            print(
                f"llm-guard not reachable at {settings.guard_api_base}. Run: make up-guardrails",
                file=sys.stderr,
            )
            return 2

        outcomes: list[GuardrailOutcome] = []
        for case in cases:
            result = await client.analyze_prompt(case.input)
            outcomes.append(
                GuardrailOutcome(
                    case_id=case.id,
                    category=case.category,
                    blocked=result.is_injection,
                )
            )
    finally:
        await client.aclose()

    scores = aggregate_guardrail_scores(outcomes)
    _write_report(profile.guardrails_report, profile.name, scores, cases, outcomes)
    print(
        f"  guardrails [{profile.name}]: "
        f"attack_block={scores.attack_block_rate:.2%} "
        f"benign_pass={scores.benign_pass_rate:.2%} "
        f"fpr={scores.false_positive_rate:.2%} "
        f"balanced={scores.balanced_accuracy:.2%} "
        f"overdefense={scores.overdefense_block_rate:.2%}"
    )
    try:
        scores.assert_at_least(profile.guardrail_minimums)
    except AssertionError as exc:
        print(f"guardrail gate failed: {exc}", file=sys.stderr)
        return 1
    return 0


def _write_report(path, profile_name, scores, cases, outcomes) -> None:
    by_id = {item.case_id: item for item in outcomes}
    when = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    mins = get_profile(profile_name).guardrail_minimums
    attack = scores.attack_block_rate
    benign = scores.benign_pass_rate
    fpr = scores.false_positive_rate
    balanced = scores.balanced_accuracy
    overdefense = scores.overdefense_block_rate
    lines = [
        f"# Guardrails — {profile_name}",
        "",
        f"_Run: {when}_",
        "",
        "Live llm-guard-api `/analyze/prompt` · metrics align with InjecGuard / Gate AI reporting.",
        "",
        "| Metric | Score | Gate |",
        "|---|---:|---:|",
        f"| Attack block rate (TPR) | {attack:.2%} | {mins.attack_block_rate:.0%} |",
        f"| Benign pass rate (TNR) | {benign:.2%} | {mins.benign_pass_rate:.0%} |",
        f"| False positive rate (FPR) | {fpr:.2%} | ≤ {mins.false_positive_rate:.0%} |",
        f"| Balanced accuracy | {balanced:.2%} | {mins.balanced_accuracy:.0%} |",
        f"| Overdefense block rate (informational) | {overdefense:.2%} | — |",
        "",
        "## Cases",
        "",
        "| ID | Category | Expected blocked | Actual blocked | Pass |",
        "|---|---|---|---|:---:|",
    ]
    for case in cases:
        outcome = by_id[case.id]
        ok = outcome.blocked == case.expected_blocked
        mark = "✓" if ok else "✗"
        lines.append(
            f"| {case.id} | {case.category} | {case.expected_blocked} | "
            f"{outcome.blocked} | {mark} |"
        )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if eval_env_file() is None:
        print("Live eval needs tests/eval/.env", file=sys.stderr)
        return 2
    suit = load_suit_settings()
    if suit.mode is not EvalMode.live:
        print("Set EVAL_MODE=live in tests/eval/.env", file=sys.stderr)
        return 2
    profile = (
        EvalProfile.investigation
        if suit.profile is EvalProfile.investigation
        else EvalProfile.default
    )
    return asyncio.run(_run_live_guardrails(profile))


if __name__ == "__main__":
    raise SystemExit(main())
