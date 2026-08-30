from agentic_eval.modules.safety.investigation import INVESTIGATION_DATASET_PATH
from agentic_eval.profiles import EvalProfile, get_profile


def test_investigation_profile_points_at_investigation_dataset() -> None:
    profile = get_profile(EvalProfile.investigation)
    assert profile.golden.dataset_path == INVESTIGATION_DATASET_PATH
    assert profile.generation_faithfulness_threshold == 0.85
    assert profile.generation_answer_relevancy_threshold == 0.70
    assert profile.retrieval_minimums.recall_at_k == 0.90
    assert profile.retrieval_stem_match is True
    assert "investigation-dossier-alpha.md" in profile.golden.known_source_files


def test_default_profile_uses_standard_corpus() -> None:
    profile = get_profile(EvalProfile.default)
    assert profile.name is EvalProfile.default
    assert profile.deepeval_identifier == "generation"
    assert profile.retrieval_stem_match is False
