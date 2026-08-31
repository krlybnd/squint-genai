ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
UV   ?= uv
UV_SYNC_FLAGS ?=

.PHONY: sync run-generation-suite run-retrieval-suite run unittest

sync:
	@test -d $(ROOT)/packages/generated/agentic-api-client \
		|| $(MAKE) -C $(ROOT) generate-openapi-clients
	$(UV) sync $(UV_SYNC_FLAGS)

run-generation-suite: sync
	mkdir -p $(ROOT)/reports/eval
	DEEPEVAL_TELEMETRY_OPT_OUT=YES DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE=180 \
		PYTHONUNBUFFERED=1 \
		$(UV) run python tests/generation/main.py

run-retrieval-suite: sync
	PYTHONUNBUFFERED=1 \
		$(UV) run python tests/retrieval/main.py

unittest: sync
	$(UV) run pytest -q tests/unittest

run: unittest
