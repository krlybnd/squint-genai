import json

import pytest
from pydantic import ValidationError

from agentic_eval.core.golden import GoldenDataset, GoldenSettings


def test_investigation_dataset_exists() -> None:
    assert GoldenSettings.investigation().dataset_path.is_file()


def test_investigation_goldens_load_and_cover_corpus() -> None:
    settings = GoldenSettings.investigation()
    loaded = GoldenDataset.load(settings)
    labeled = loaded.labeled
    abstention = loaded.abstention

    assert len(labeled) >= 8
    assert len(abstention) >= 3
    assert {g.expected_source_file for g in labeled} <= set(settings.known_source_files)
    assert any(len(g.relevant_sources) >= 2 for g in labeled)
    assert any(g.required_phrases for g in labeled)
    raw = json.loads(settings.dataset_path.read_text(encoding="utf-8"))
    cross_raw = [item for item in raw if "cross-doc" in item.get("tags", [])]
    assert cross_raw
    for item in cross_raw:
        sources = item.get("expected_source_files") or [item["expected_source_file"]]
        assert len(sources) >= 2


def test_investigation_abstention_traps_decoy_questions() -> None:
    settings = GoldenSettings.investigation()
    abstention = GoldenDataset.load(settings).abstention
    blob = " ".join(g.input.lower() for g in abstention)

    assert "environmental" in blob or "kah-kv" in blob
    assert "mixture-of-experts" in blob


def test_investigation_labeled_includes_cross_doc_and_pii() -> None:
    raw = json.loads(GoldenSettings.investigation().dataset_path.read_text(encoding="utf-8"))
    tags = {tag for item in raw for tag in item.get("tags", [])}

    assert "cross-doc" in tags
    assert "pii" in tags
    assert "decoy-trap" in tags


def test_investigation_shared_facts_label_alpha_and_beta() -> None:
    raw = json.loads(GoldenSettings.investigation().dataset_path.read_text(encoding="utf-8"))
    for tag in ("F-05", "F-06", "F-07"):
        items = [item for item in raw if tag in item.get("tags", [])]
        assert items, f"missing golden tagged {tag}"
        for item in items:
            sources = item.get("expected_source_files") or [item["expected_source_file"]]
            assert "investigation-dossier-alpha.md" in sources
            assert "investigation-dossier-beta.md" in sources
            assert "investigation-dossier-gamma-decoy.md" not in sources


def test_investigation_iban_required_phrase_is_complete() -> None:
    full_iban = "HU68 KAMU 0001 2345 6789 0123 4567"
    raw = json.loads(GoldenSettings.investigation().dataset_path.read_text(encoding="utf-8"))
    iban_items = [item for item in raw if "IBAN" in item.get("input", "")]
    assert iban_items
    for item in iban_items:
        phrases = item.get("required_phrases", [])
        assert full_iban in phrases
        assert phrases != ["HU68"]


def test_investigation_rejects_unknown_source(tmp_path) -> None:
    dataset = tmp_path / "dataset.json"
    dataset.write_text(
        json.dumps(
            [
                {
                    "input": "q",
                    "expected_output": "a" * 24,
                    "expected_source_file": "investigation-dossier-alpha.md",
                }
            ]
        ),
        encoding="utf-8",
    )
    settings = GoldenSettings(dataset_path=dataset, known_source_files=("other.md",))

    with pytest.raises(ValidationError):
        GoldenDataset.load(settings)
