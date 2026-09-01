ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
NPM  ?= npm
NPM_WORKSPACE := agentic-rag-eval-demo-studio

.PHONY: install prepare record help

help: ## Show targets
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-24s %s\n", $$1, $$2}'

install: ## npm ci (root workspace lockfile)
	cd "$(ROOT)" && $(NPM) ci

prepare: install ## Index three dossiers in Tenant B (not recorded)
	cd "$(ROOT)" && $(NPM) run prepare-corpus -w $(NPM_WORKSPACE)

record: install ## Record @demo walkthrough → .reports/demo-studio/walkthrough/
	cd "$(ROOT)" && $(NPM) run record -w $(NPM_WORKSPACE)
