from deepeval.test_case import LLMTestCase

from agentic_eval.core.deepeval import AbstentionMetric, RequiredPhrasesMetric
from agentic_eval.core.deepeval.metrics import clean_refusal, guard_block

_MARKERS = ("cannot find", "not available")


def test_guard_block_matches_security_copy() -> None:
    # Arrange / Act / Assert
    assert guard_block("Rejected by the security check.")
    assert guard_block("Prompt injection detected.")
    assert not guard_block("The IBAN is HU68 ACCT-000044.")


def test_required_phrases_skips_abstention_goldens() -> None:
    # Arrange
    metric = RequiredPhrasesMetric()
    case = LLMTestCase(
        input="What criminal classification applies?",
        actual_output="I cannot find that in the materials.",
        tags=["abstention"],
        metadata={"required_phrases": ["KAH-KV-2023/4419"]},
    )

    # Act
    score = metric.measure(case)

    # Assert
    assert score == 1.0
    assert metric.skipped is True
    assert metric.success is True


def test_required_phrases_fails_when_identifier_missing() -> None:
    # Arrange
    metric = RequiredPhrasesMetric()
    case = LLMTestCase(
        input="What IBAN appears in the financial trace export?",
        actual_output="A Hungarian IBAN is listed.",
        tags=["labeled"],
        metadata={"required_phrases": ["HU68123456789012345678901234"]},
    )

    # Act
    score = metric.measure(case)

    # Assert
    assert score == 0.0
    assert metric.success is False
    assert "HU68123456789012345678901234" in metric.reason


def test_required_phrases_passes_when_all_present() -> None:
    # Arrange
    metric = RequiredPhrasesMetric()
    case = LLMTestCase(
        input="What IBAN appears in the financial trace export?",
        actual_output="The IBAN is HU68123456789012345678901234.",
        tags=["labeled"],
        metadata={"required_phrases": ["HU68123456789012345678901234"]},
    )

    # Act
    score = metric.measure(case)

    # Assert
    assert score == 1.0
    assert metric.success is True
    assert metric.reason == "ok"


def test_abstention_metric_requires_clean_refusal_on_abstention_tag() -> None:
    # Arrange
    metric = AbstentionMetric(markers=_MARKERS)
    case = LLMTestCase(
        input="What mixture-of-experts routing algorithm is used?",
        actual_output="I cannot find that in the dossiers.",
        tags=["abstention"],
    )

    # Act
    score = metric.measure(case)

    # Assert
    assert score == 1.0
    assert metric.success is True


def test_abstention_metric_fails_labeled_false_refusal() -> None:
    # Arrange
    metric = AbstentionMetric(markers=_MARKERS)
    case = LLMTestCase(
        input="What IBAN appears in the financial trace export?",
        actual_output="I cannot find an IBAN in the materials.",
        tags=["labeled"],
    )

    # Act
    score = metric.measure(case)

    # Assert
    assert score == 0.0
    assert metric.reason == "False abstention."


def test_clean_refusal_rejects_guard_copy_and_fact_leak() -> None:
    # Arrange / Act / Assert
    assert not clean_refusal(
        "Rejected by the security check.",
        _MARKERS,
        "What mixture-of-experts routing algorithm is used?",
    )
    assert not clean_refusal(
        "I cannot find ART-2024/8812 in the materials.",
        _MARKERS,
        "What mixture-of-experts routing algorithm is used?",
    )
    assert clean_refusal(
        "That information is not available in the indexed dossiers.",
        _MARKERS,
        "What mixture-of-experts routing algorithm is used?",
    )
