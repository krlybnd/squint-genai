# Node project template. Set PROJECT_NAME, ROOT, NPM_WORKSPACE (package.json name).
# Include after report.mk.

NPM ?= npm
NPX ?= npx

.PHONY: install lint unit-test integration-test licenses build clean help test

help: ## Show targets
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) $(dir $(lastword $(MAKEFILE_LIST)))Makefile 2>/dev/null | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  %-22s %s\n", $$1, $$2}' | sort -u

install: ## npm ci (root workspace lockfile)
	cd "$(ROOT)" && $(NPM) ci

test: unit-test ## Alias

unit-test: _report-dirs-unit install ## npm test (Vitest / package scripts)
	@if cd "$(ROOT)" && $(NPM) pkg get scripts.test -w $(NPM_WORKSPACE) 2>/dev/null | grep -qv '^{}'; then \
		cd "$(ROOT)" && $(NPM) run test -w $(NPM_WORKSPACE); \
	else \
		$(call write-empty-junit,unit,$(UNIT_TEST_REPORT)); \
		echo "$(PROJECT_NAME): no npm test script"; \
	fi

integration-test: _report-dirs-integration ## Playwright / integration (override in e2e)
	$(call write-empty-junit,integration,$(INTEGRATION_TEST_REPORT))
	@echo "$(PROJECT_NAME): no integration tests (skipped)"

lint: install ## eslint + stylelint + tsc (per package.json)
	cd "$(ROOT)" && $(NPM) run lint -w $(NPM_WORKSPACE)

build: install ## Production build
	cd "$(ROOT)" && $(NPM) run build -w $(NPM_WORKSPACE)

licenses: _report-dirs-sbom install ## CycloneDX SBOM
	@mkdir -p $(LICENSES_DIR)
	cd "$(PROJECT_DIR)" && $(NPX) --yes @cyclonedx/cyclonedx-npm --output-file $(SBOM_REPORT) --spec-version 1.5
	@cp $(SBOM_REPORT) $(LICENSES_DIR)/$(PROJECT_NAME).cdx.json
	@echo "Wrote $(SBOM_REPORT)"

clean: ## Remove node_modules and build artifacts
	@rm -rf node_modules dist .features-gen coverage
