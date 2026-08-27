ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
UV   ?= uv
ENV_FILE := $(ROOT)/.env

.PHONY: sync install run run-live format help

help: ## Show targets
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-18s %s\n", $$1, $$2}'

sync: ## uv sync
	$(UV) sync $(UV_SYNC_FLAGS)

install: sync ## Alias

run: sync ## Offline dataset + metric checks
	$(UV) run pytest -q -m "not eval and not integration"

run-live: sync ## DeepEval + retrieval IR against live stack (loads repo .env)
	@set -a; [ -f "$(ENV_FILE)" ] && . "$(ENV_FILE)"; set +a; \
	DEEPEVAL_TELEMETRY_OPT_OUT=YES EVAL_MODE=live $(UV) run pytest -q test_retrieval_eval.py; \
	DEEPEVAL_TELEMETRY_OPT_OUT=YES EVAL_MODE=live $(UV) run deepeval test run test_rag_eval.py -q

format: sync ## Auto-format
	$(UV) run ruff format
