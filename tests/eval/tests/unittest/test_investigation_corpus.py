from agentic_eval.modules.safety.corpus import (
    load_investigation_corpus,
    validate_investigation_corpus,
)
from agentic_eval.modules.safety.fixtures import (
    INVESTIGATION_PII_ENTITIES,
    find_forbidden_real_entities,
    scan_plaintext_pii,
)


def test_investigation_corpus_passes_validation() -> None:
    errors = validate_investigation_corpus()
    assert errors == [], errors


def test_investigation_corpus_contains_pii_fixtures_for_vault() -> None:
    corpus = load_investigation_corpus()
    alpha = corpus["investigation-dossier-alpha.md"]

    results = scan_plaintext_pii(alpha)
    found = [item.entity for item in results if item.found]

    assert "Esther Szabo" in found
    assert "99999999-9-99" in found
    assert "eszabo.eval-fixture@example.invalid" in found


def test_gamma_decoy_isolated_from_alpha_pii_values() -> None:
    gamma = load_investigation_corpus()["investigation-dossier-gamma-decoy.md"]

    assert "99999999-9-99" not in gamma
    assert "eszabo.eval-fixture@example.invalid" not in gamma
    assert "+36 99 000 0001" not in gamma
    assert find_forbidden_real_entities(gamma) == []


def test_corpus_has_no_real_entity_patterns() -> None:
    combined = "\n".join(load_investigation_corpus().values())
    assert find_forbidden_real_entities(combined) == []


def test_pii_entity_list_is_non_empty() -> None:
    assert len(INVESTIGATION_PII_ENTITIES) >= 5
