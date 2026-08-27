from agentic_eval.modules.generation.evaluators import looks_like_refusal
from agentic_eval.modules.generation.settings import DEFAULT_REFUSAL_MARKERS, GenerationSettings
from suit.settings import SUIT_REFUSAL_MARKERS


def test_looks_like_refusal_uses_generation_defaults() -> None:
    # Assert
    assert looks_like_refusal("I cannot find it in the indexed excerpts.")
    assert looks_like_refusal("There is no relevant information in the answer.")
    assert not looks_like_refusal("The provided context does not include Article I.")


def test_looks_like_refusal_honors_suit_markers() -> None:
    # Assert
    assert looks_like_refusal(
        "The provided context does not include Article I.",
        SUIT_REFUSAL_MARKERS,
    )
    assert looks_like_refusal(
        "The provided content does not contain that fact.",
        SUIT_REFUSAL_MARKERS,
    )
    assert looks_like_refusal(
        "That fact is not specified in the indexed excerpts.",
        SUIT_REFUSAL_MARKERS,
    )


def test_looks_like_refusal_ignores_substantive_negation() -> None:
    # Assert
    assert not looks_like_refusal(
        "No. NIST AI RMF 1.0 is a voluntary framework, not a binding regulation.",
        SUIT_REFUSAL_MARKERS,
    )


def test_generation_settings_defaults_are_a_short_list() -> None:
    # Arrange / Act
    settings = GenerationSettings()

    # Assert
    assert settings.refusal_markers == DEFAULT_REFUSAL_MARKERS
    assert len(settings.refusal_markers) < len(SUIT_REFUSAL_MARKERS)
