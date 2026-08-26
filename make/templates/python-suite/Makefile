ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../../..
UV   ?= uv

.PHONY: sync install run format help

help: ## Show targets
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-18s %s\n", $$1, $$2}'

sync: ## uv sync
	$(UV) sync $(UV_SYNC_FLAGS)

install: sync ## Alias

run: sync ## Run suite (override in project Makefile)
	@echo "Override run target"

format: sync ## Auto-format
	$(UV) run ruff format
