# Python project template. Set PROJECT_NAME, ROOT; optional PACKAGE, PORT, UV_PACKAGE.
# Include after report.mk.

UV              ?= uv
PROJECT_DIR     ?= $(CURDIR)
COVERAGE_RCFILE ?= $(PROJECT_DIR)/pyproject.toml
UNIT_TEST_DIR   ?= tests/unittest
UV_SYNC_FLAGS   ?= --frozen
UV_SBOM_FLAGS   ?= --format cyclonedx1.5 --preview-features sbom-export

.PHONY: sync lint format unit-test unit-test-coverage licenses clean help test

help: ## Show targets
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) $(dir $(lastword $(MAKEFILE_LIST)))Makefile 2>/dev/null | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  %-22s %s\n", $$1, $$2}' | sort -u

sync: ## uv sync (project-local lockfile)
	$(UV) sync $(UV_SYNC_FLAGS)

lint: ## Ruff check + format + mypy
	$(UV) run ruff check
	$(UV) run ruff format --check
	$(UV) run mypy --config-file $(ROOT)/mypy.ini src
	@if grep -RInE --include='*.py' '__getattr__|\bgetattr\(|\bhasattr\(' src; then \
		echo "getattr/hasattr is banned: bind the type instead of duck-typing"; \
		exit 1; \
	fi

format: ## Auto-format with ruff
	$(UV) run ruff check --fix
	$(UV) run ruff format

test: unit-test ## Alias

unit-test: _report-dirs-unit ## unittest → .reports/<stack>/<name>/unit-test.xml
	@if [ -d "$(UNIT_TEST_DIR)" ]; then \
		COVERAGE_RCFILE=$(COVERAGE_RCFILE) $(UV) run pytest -q \
			--junitxml=$(UNIT_TEST_REPORT); \
	else \
		$(call write-empty-junit,unit,$(UNIT_TEST_REPORT)); \
		echo "$(PROJECT_NAME): no $(UNIT_TEST_DIR)"; \
	fi

unit-test-coverage: _report-dirs-unit _report-dirs-coverage ## HTML coverage report
	@if [ ! -d "$(UNIT_TEST_DIR)" ]; then \
		echo "$(PROJECT_NAME): no $(UNIT_TEST_DIR) (coverage skipped)"; \
	else \
		COVERAGE_RCFILE=$(COVERAGE_RCFILE) $(UV) run coverage run \
			--data-file=$(COVERAGE_DATA_FILE) \
			-m pytest -q; \
		COVERAGE_RCFILE=$(COVERAGE_RCFILE) $(UV) run coverage html \
			--data-file=$(COVERAGE_DATA_FILE) -d $(COVERAGE_HTML_DIR); \
		COVERAGE_RCFILE=$(COVERAGE_RCFILE) $(UV) run coverage report \
			--data-file=$(COVERAGE_DATA_FILE); \
	fi

licenses: _report-dirs-sbom ## CycloneDX SBOM
	@mkdir -p $(LICENSES_DIR)
	$(UV) export $(UV_SBOM_FLAGS) -o $(SBOM_REPORT)
	@cp $(SBOM_REPORT) $(LICENSES_DIR)/$(PROJECT_NAME).cdx.json
	@echo "Wrote $(SBOM_REPORT)"

clean: ## Remove local venv and caches
	@rm -rf .venv .pytest_cache .coverage htmlcov
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
