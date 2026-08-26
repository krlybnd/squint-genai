import json
from pathlib import Path

from metrics import rag_metrics

DATASET = Path(__file__).resolve().parent / "dataset.json"


def test_eval_dataset_is_grounded_in_sample_corpus() -> None:
    goldens = json.loads(DATASET.read_text())
    assert len(goldens) >= 15
    inputs = [item["input"] for item in goldens]
    assert len(inputs) == len(set(inputs))
    blob = " ".join(inputs).lower()
    assert "what services make up the platform" not in blob
    for needle in ("transformer", "rag-sequence", "constitution", "artemis", "nist"):
        assert needle in blob
    for item in goldens:
        assert item["expected_output"].strip()
        assert len(item["expected_output"]) > 20


def test_rag_metrics_include_retrieval_judges() -> None:
    import inspect

    source = inspect.getsource(rag_metrics)
    assert "ContextualPrecisionMetric" in source
    assert "ContextualRecallMetric" in source
