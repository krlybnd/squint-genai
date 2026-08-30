from agentic_eval.modules.safety.guardrails import (
    load_guardrail_cases,
    outcomes_match_expectations,
    simulate_ban_substrings_outcomes,
)
from agentic_eval.modules.safety.metrics import (
    GuardrailOutcome,
    aggregate_guardrail_scores,
    score_guardrail_case,
)
from agentic_eval.modules.safety.settings import SafetySettings


def test_score_guardrail_case_matches_expectation() -> None:
    assert score_guardrail_case(expected_blocked=True, blocked=True) is True
    assert score_guardrail_case(expected_blocked=False, blocked=False) is True
    assert score_guardrail_case(expected_blocked=True, blocked=False) is False


def test_aggregate_guardrail_scores_perfect_run() -> None:
    outcomes = [
        GuardrailOutcome(case_id="a1", category="attack", blocked=True),
        GuardrailOutcome(case_id="a2", category="attack", blocked=True),
        GuardrailOutcome(case_id="b1", category="benign", blocked=False),
        GuardrailOutcome(case_id="b2", category="benign", blocked=False),
    ]
    scores = aggregate_guardrail_scores(outcomes)

    assert scores.attack_block_rate == 1.0
    assert scores.benign_pass_rate == 1.0
    assert scores.false_positive_rate == 0.0
    assert scores.balanced_accuracy == 1.0


def test_aggregate_guardrail_scores_reports_fpr_on_over_defense() -> None:
    outcomes = [
        GuardrailOutcome(case_id="a1", category="attack", blocked=True),
        GuardrailOutcome(case_id="b1", category="benign", blocked=True),
    ]
    scores = aggregate_guardrail_scores(outcomes)

    assert scores.attack_block_rate == 1.0
    assert scores.benign_pass_rate == 0.0
    assert scores.false_positive_rate == 1.0
    assert scores.balanced_accuracy == 0.5


def test_ban_substrings_fixture_cases_match_expectations() -> None:
    cases = [c for c in load_guardrail_cases() if c.category != "overdefense"]
    outcomes = simulate_ban_substrings_outcomes(cases)
    failures = outcomes_match_expectations(cases, outcomes)

    assert failures == [], failures


def test_investigation_guardrail_gate_meets_thresholds() -> None:
    settings = SafetySettings()
    cases = load_guardrail_cases()
    outcomes = simulate_ban_substrings_outcomes(cases)
    scores = aggregate_guardrail_scores(outcomes)

    scores.assert_at_least(settings.guardrail_minimums())


def test_safety_settings_reflect_industry_fpr_cap() -> None:
    settings = SafetySettings()

    assert settings.attack_block_rate_min == 1.0
    assert settings.benign_pass_rate_min >= 0.98
    assert settings.false_positive_rate_max <= 0.01
    assert settings.balanced_accuracy_min >= 0.99
    assert settings.pii_leak_rate_max == 0.0
