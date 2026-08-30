ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
UV   ?= uv

.PHONY: sync install run run-live eval-live run-live-generation run-live-investigation run-live-investigation-generation run-live-guardrails format help

help: ## Show targets
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-18s %s\n", $$1, $$2}'

sync: ## uv sync
	$(UV) sync $(UV_SYNC_FLAGS)

install: sync ## Alias

run: sync ## Offline dataset + metric + Pydantic Evals checks
	$(UV) run pytest -q tests/unittest

run-live: sync ## Retrieval IR gate (no judge LLM — seconds, not minutes)
	DEEPEVAL_TELEMETRY_OPT_OUT=YES EVAL_MODE=live \
		$(UV) run pytest -s tests/suit/test_retrieval_eval.py

eval-live: run-live ## Same as run-live (root `make eval-live` also works)

run-live-generation: sync ## DeepEval generation gate (slow: graph + Faithfulness/Relevancy judges)
	DEEPEVAL_TELEMETRY_OPT_OUT=YES DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE=180 \
		EVAL_MODE=live PYTHONPATH=tests PYTHONUNBUFFERED=1 \
		$(UV) run python tests/suit/run_generation_eval.py

run-live-investigation: sync ## Investigation retrieval IR (live Qdrant, indexed resources/eval/)
	DEEPEVAL_TELEMETRY_OPT_OUT=YES EVAL_MODE=live EVAL_PROFILE=investigation \
		$(UV) run pytest -s tests/suit/test_investigation_retrieval_eval.py

eval-live-investigation: run-live-investigation ## Alias

run-live-investigation-generation: sync ## Investigation DeepEval gate (LLM judge, slow)
	DEEPEVAL_TELEMETRY_OPT_OUT=YES DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE=180 \
		EVAL_MODE=live PYTHONPATH=tests PYTHONUNBUFFERED=1 \
		$(UV) run python tests/suit/run_investigation_generation_eval.py

run-live-guardrails: sync ## Live llm-guard HTTP metrics (TPR/FPR/balanced accuracy)
	DEEPEVAL_TELEMETRY_OPT_OUT=YES EVAL_MODE=live \
		PYTHONPATH=tests PYTHONUNBUFFERED=1 \
		$(UV) run python tests/suit/run_guardrails_eval.py

format: sync ## Auto-format
	$(UV) run ruff check --fix
	$(UV) run ruff format
