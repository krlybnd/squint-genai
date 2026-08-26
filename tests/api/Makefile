ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
NPM  ?= npm

.PHONY: install run lint help

help: ## Show targets
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-18s %s\n", $$1, $$2}'

install: ## npm ci + generate OpenAPI types
	$(NPM) ci

lint: install ## tsc against generated OpenAPI types
	$(NPM) run lint

run: install ## Gherkin API acceptance (needs make up)
	$(NPM) test
