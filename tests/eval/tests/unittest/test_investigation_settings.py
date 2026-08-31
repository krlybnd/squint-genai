from agentic_eval.core.golden import GoldenSettings
from generation.settings import GenerationGates
from retrieval.settings import RetrievalGates


def test_investigation_golden_settings_point_at_dossiers() -> None:
    golden = GoldenSettings.investigation()
    assert golden.dataset_path.name == "dataset-investigation.json"
    assert golden.dataset_path.parent.name == "eval"
    assert "investigation-dossier-alpha.md" in golden.known_source_files
    assert "investigation-dossier-alpha.pdf" in golden.known_source_files


def test_investigation_gates_live_on_generation_and_retrieval_defaults() -> None:
    generation = GenerationGates()
    assert generation.faithfulness_threshold == 0.85
    assert generation.answer_relevancy_threshold == 0.70
    assert generation.correctness_threshold == 0.80
    assert RetrievalGates().minimums.document_recall_at_k == 0.90
    assert RetrievalGates().minimums.chunk_precision_at_k == 0.85
