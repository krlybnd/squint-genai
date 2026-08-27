import json

import pytest
from pydantic import ValidationError

from agentic_eval.core.goldendata import (
    DEFAULT_DATASET_PATH,
    DEFAULT_SOURCE_FILES,
    AbstentionGolden,
    GoldenSettings,
    LabeledGolden,
    load_goldens,
)


def test_eval_dataset_is_grounded_in_sample_corpus() -> None:
    # Arrange
    goldens = json.loads(DEFAULT_DATASET_PATH.read_text(encoding="utf-8"))
    inputs = [item["input"] for item in goldens]
    blob = " ".join(inputs).lower()

    # Assert
    assert len(goldens) >= 15
    assert len(inputs) == len(set(inputs))
    assert "what services make up the platform" not in blob
    for needle in ("transformer", "rag-sequence", "constitution", "artemis", "nist"):
        assert needle in blob
    for item in goldens:
        assert item["expected_output"].strip()
        assert len(item["expected_output"]) > 20


def test_eval_dataset_labels_retrieval_sources() -> None:
    # Arrange
    loaded = load_goldens()
    labeled = [golden for golden in loaded if isinstance(golden, LabeledGolden)]
    abstention = [golden for golden in loaded if isinstance(golden, AbstentionGolden)]
    blob = " ".join(golden.input.lower() for golden in abstention)

    # Assert
    assert len(labeled) == 20
    assert len(abstention) >= 3
    assert {golden.expected_source_file for golden in labeled} == set(DEFAULT_SOURCE_FILES)
    assert "capital of france" not in blob
    assert any(needle in blob for needle in ("transformer", "artemis", "constitution"))


def test_dataset_path_lives_in_eval_root() -> None:
    # Assert
    assert DEFAULT_DATASET_PATH.name == "dataset.json"
    assert DEFAULT_DATASET_PATH.parent.name == "eval"
    assert DEFAULT_DATASET_PATH.is_file()


def test_labeled_golden_rejects_unknown_source() -> None:
    # Act / Assert
    with pytest.raises(ValidationError):
        LabeledGolden(
            input="q",
            expected_output="a" * 24,
            expected_source_file="not-in-corpus.pdf",
        )


def test_labeled_golden_accepts_override_source_files() -> None:
    # Arrange / Act
    golden = LabeledGolden.model_validate(
        {
            "input": "q",
            "expected_output": "a" * 24,
            "expected_source_file": "custom.pdf",
        },
        context={"known_source_files": ("custom.pdf",)},
    )

    # Assert
    assert golden.expected_source_file == "custom.pdf"


def test_load_goldens_honors_settings_source_files(tmp_path) -> None:
    # Arrange
    dataset = tmp_path / "dataset.json"
    dataset.write_text(
        json.dumps(
            [
                {
                    "input": "q",
                    "expected_output": "a" * 24,
                    "expected_source_file": "custom.pdf",
                }
            ]
        ),
        encoding="utf-8",
    )
    settings = GoldenSettings(dataset_path=dataset, known_source_files=("custom.pdf",))

    # Act
    loaded = load_goldens(settings=settings)

    # Assert
    assert len(loaded) == 1
    assert isinstance(loaded[0], LabeledGolden)
    assert loaded[0].expected_source_file == "custom.pdf"


def test_load_goldens_rejects_source_not_in_settings(tmp_path) -> None:
    # Arrange
    dataset = tmp_path / "dataset.json"
    dataset.write_text(
        json.dumps(
            [
                {
                    "input": "q",
                    "expected_output": "a" * 24,
                    "expected_source_file": DEFAULT_SOURCE_FILES[0],
                }
            ]
        ),
        encoding="utf-8",
    )
    settings = GoldenSettings(dataset_path=dataset, known_source_files=("custom.pdf",))

    # Act / Assert
    with pytest.raises(ValidationError):
        load_goldens(settings=settings)


def test_abstention_golden_rejects_source_file() -> None:
    # Act / Assert
    with pytest.raises(ValidationError):
        AbstentionGolden.model_validate(
            {
                "input": "q",
                "expected_output": "a" * 24,
                "expect_abstention": True,
                "expected_source_file": "us-constitution.pdf",
            }
        )
