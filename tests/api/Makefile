ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
NPM  ?= npm
NPM_WORKSPACE := agentic-rag-eval-api

.PHONY: install run lint help

help: ## Show targets
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-18s %s\n", $$1, $$2}'

install: ## npm ci (root workspace lockfile)
	cd "$(ROOT)" && $(NPM) ci

lint: install ## tsc against generated OpenAPI types
	cd "$(ROOT)" && $(NPM) run lint -w $(NPM_WORKSPACE)

run: install ## Gherkin API acceptance (needs make up)
	cd "$(ROOT)" && $(NPM) run test -w $(NPM_WORKSPACE)
