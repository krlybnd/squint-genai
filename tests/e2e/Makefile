ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
NPM  ?= npm
NPM_WORKSPACE := agentic-rag-eval-e2e

.PHONY: install run help

help: ## Show targets
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-18s %s\n", $$1, $$2}'

install: ## npm ci (root workspace lockfile)
	cd "$(ROOT)" && $(NPM) ci

run: install ## Playwright BDD (needs make up-ui)
	cd "$(ROOT)" && $(NPM) run test -w $(NPM_WORKSPACE)
