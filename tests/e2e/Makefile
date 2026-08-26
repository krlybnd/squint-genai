ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
NPM  ?= npm

.PHONY: install run help

help: ## Show targets
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-18s %s\n", $$1, $$2}'

install: ## npm ci
	$(NPM) ci

run: install ## Playwright BDD (needs make up-ui)
	$(NPM) test
