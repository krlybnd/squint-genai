ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
NPM  ?= npm
NPM_WORKSPACE := agentic-rag-eval-e2e

.PHONY: install run run-smoke-suite run-regression-suite help

help: ## Show targets
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-24s %s\n", $$1, $$2}'

install: ## npm ci (root workspace lockfile)
	cd "$(ROOT)" && $(NPM) ci

run-smoke-suite: install ## @smoke (needs make up-auth)
	cd "$(ROOT)" && $(NPM) run test:smoke -w $(NPM_WORKSPACE)

run-regression-suite: install ## @regression (needs make up-auth)
	cd "$(ROOT)" && $(NPM) run test:regression -w $(NPM_WORKSPACE)

run: install ## smoke then regression
	cd "$(ROOT)" && $(NPM) run test:smoke -w $(NPM_WORKSPACE)
	cd "$(ROOT)" && $(NPM) run test:regression -w $(NPM_WORKSPACE)
