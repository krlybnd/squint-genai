import json

import pytest
from pydantic import ValidationError

from agentic_eval.core.golden import (
    AbstentionGolden,
    GoldenDataset,
    GoldenSettings,
    LabeledGolden,
)


def test_eval_dataset_is_grounded_in_sample_corpus() -> None:
    # Arrange
    goldens = json.loads(GoldenSettings().dataset_path.read_text(encoding="utf-8"))
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
    loaded = GoldenDataset.load()
    blob = " ".join(golden.input.lower() for golden in loaded.abstention)

    # Assert
    assert len(loaded.labeled) == 20
    assert len(loaded.abstention) >= 3
    assert {golden.expected_source_file for golden in loaded.labeled} == set(
        GoldenSettings().known_source_files
    )
    assert "capital of france" not in blob
    assert any(needle in blob for needle in ("transformer", "artemis", "constitution"))


def test_dataset_path_lives_in_eval_root() -> None:
    # Assert
    path = GoldenSettings().dataset_path
    assert path.name == "dataset.json"
    assert path.parent.name == "eval"
    assert path.is_file()


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


def test_labeled_golden_relevant_sources_defaults_to_primary() -> None:
    golden = LabeledGolden(
        input="q",
        expected_output="a" * 24,
        expected_source_file="attention-is-all-you-need.pdf",
    )
    assert golden.relevant_sources == ("attention-is-all-you-need.pdf",)


def test_labeled_golden_relevant_sources_uses_explicit_list() -> None:
    golden = LabeledGolden.model_validate(
        {
            "input": "q",
            "expected_output": "a" * 24,
            "expected_source_file": "custom.pdf",
            "expected_source_files": ["custom.pdf", "other.pdf"],
        },
        context={"known_source_files": ("custom.pdf", "other.pdf")},
    )
    assert golden.relevant_sources == ("custom.pdf", "other.pdf")


def test_labeled_golden_case_name_truncates() -> None:
    # Arrange
    golden = LabeledGolden(
        input="x" * 80,
        expected_output="a" * 24,
        expected_source_file="attention-is-all-you-need.pdf",
    )

    # Act / Assert
    assert golden.case_name(3).startswith("03:")
    assert golden.case_name(3).endswith("...")
    assert len(golden.case_name(3)) == 3 + 72


def test_golden_dataset_parse_dispatches_on_matches() -> None:
    # Arrange
    sources = ("custom.pdf",)
    labeled_raw = {
        "input": "q",
        "expected_output": "a" * 24,
        "expected_source_file": "custom.pdf",
    }
    abstention_raw = {
        "input": "q",
        "expected_output": "a" * 24,
        "expect_abstention": True,
    }

    # Act
    labeled = GoldenDataset.parse(labeled_raw, known_source_files=sources)
    abstention = GoldenDataset.parse(abstention_raw, known_source_files=sources)

    # Assert
    assert isinstance(labeled, LabeledGolden)
    assert isinstance(abstention, AbstentionGolden)


def test_golden_dataset_honors_settings_source_files(tmp_path) -> None:
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
    loaded = GoldenDataset.load(settings)

    # Assert
    assert len(loaded) == 1
    assert isinstance(loaded[0], LabeledGolden)
    assert loaded[0].expected_source_file == "custom.pdf"


def test_golden_dataset_rejects_source_not_in_settings(tmp_path) -> None:
    # Arrange
    dataset = tmp_path / "dataset.json"
    dataset.write_text(
        json.dumps(
            [
                {
                    "input": "q",
                    "expected_output": "a" * 24,
                    "expected_source_file": GoldenSettings().known_source_files[0],
                }
            ]
        ),
        encoding="utf-8",
    )
    settings = GoldenSettings(dataset_path=dataset, known_source_files=("custom.pdf",))

    # Act / Assert
    with pytest.raises(ValidationError):
        GoldenDataset.load(settings)


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
