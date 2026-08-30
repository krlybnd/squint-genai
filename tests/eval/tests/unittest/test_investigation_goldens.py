import json

import pytest
from pydantic import ValidationError

from agentic_eval.core.goldendata import (
    AbstentionGolden,
    GoldenSettings,
    LabeledGolden,
    load_goldens,
)
from agentic_eval.modules.safety.investigation import (
    INVESTIGATION_DATASET_PATH,
    INVESTIGATION_SOURCE_FILES,
)


def test_investigation_dataset_exists() -> None:
    assert INVESTIGATION_DATASET_PATH.is_file()


def test_investigation_goldens_load_and_cover_corpus() -> None:
    settings = GoldenSettings(
        dataset_path=INVESTIGATION_DATASET_PATH,
        known_source_files=INVESTIGATION_SOURCE_FILES,
    )
    loaded = load_goldens(settings=settings)
    labeled = [g for g in loaded if isinstance(g, LabeledGolden)]
    abstention = [g for g in loaded if isinstance(g, AbstentionGolden)]

    assert len(labeled) >= 8
    assert len(abstention) >= 3
    assert {g.expected_source_file for g in labeled} <= set(INVESTIGATION_SOURCE_FILES)


def test_investigation_abstention_traps_decoy_questions() -> None:
    settings = GoldenSettings(
        dataset_path=INVESTIGATION_DATASET_PATH,
        known_source_files=INVESTIGATION_SOURCE_FILES,
    )
    abstention = [g for g in load_goldens(settings=settings) if isinstance(g, AbstentionGolden)]
    blob = " ".join(g.input.lower() for g in abstention)

    assert "environmental" in blob or "kah-kv" in blob
    assert "mixture-of-experts" in blob


def test_investigation_labeled_includes_cross_doc_and_pii() -> None:
    raw = json.loads(INVESTIGATION_DATASET_PATH.read_text(encoding="utf-8"))
    tags = {tag for item in raw for tag in item.get("tags", [])}

    assert "cross-doc" in tags
    assert "pii" in tags
    assert "decoy-trap" in tags


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
        load_goldens(settings=settings)
