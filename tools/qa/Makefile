# Quality recipes — no Docker. Host or `docker compose --profile qa run --rm qa make <target>`.
# Canonical names: unittest, system-test, license, eval-live, e2e.
# unittest always runs coverage and combines it. CI still calls coverage-combine
# after downloading per-project artifacts (no full unittest in that job).

QA_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
ROOT ?= $(abspath $(QA_DIR)/../..)

.PHONY: unittest test test-unit coverage-combine
.PHONY: lint format
.PHONY: system-test api-test test-api
.PHONY: license licenses
.PHONY: eval-live eval-live-generation
.PHONY: e2e

unittest: ## All unit tests (every project) + combined coverage
	@set -e; for p in $(PYTHON_LIBS) $(PYTHON_SERVICES); do echo "==> $$p unit-test-coverage"; $(MAKE) -C $$p unit-test-coverage; done
	@set -e; for p in $(NODE_PROJECTS); do echo "==> $$p unit-test"; $(MAKE) -C $$p unit-test; done
	@$(MAKE) coverage-combine

test: unittest
test-unit: unittest

# CI: combine already-produced .coverage files. Not a separate local coverage mode.
coverage-combine:
	@mkdir -p $(REPORTS_DIR)/coverage/combined
	@cov_files=""; \
	for name in $(PYTHON_REPORT_NAMES); do \
		f="$(REPORTS_DIR)/python/$$name/.coverage"; \
		if [ -f "$$f" ]; then cov_files="$$cov_files $$f"; fi; \
	done; \
	if [ -n "$$cov_files" ]; then \
		rm -f $(REPORTS_DIR)/coverage/combined/.coverage; \
		cd $(ROOT)/packages/shared && $(UV) run coverage combine --keep $$cov_files; \
		$(UV) run coverage html -d $(REPORTS_DIR)/coverage/combined; \
		$(UV) run coverage report || true; \
		echo "Coverage HTML: $(REPORTS_DIR)/coverage/combined/index.html"; \
	else \
		echo "No coverage data files under $(REPORTS_DIR)/python/*/\.coverage" >&2; \
	fi

lint: ## Lint libs, services, and UI
	@set -e; for p in $(PYTHON_PROJECTS); do $(MAKE) -C $$p lint; done
	@set -e; for p in $(NODE_PROJECTS); do $(MAKE) -C $$p lint; done

format: ## Auto-format Python (libs, services)
	@set -e; for p in $(PYTHON_PROJECTS); do $(MAKE) -C $$p format; done

# Offline eval dataset unittest is not a gate (`make -C tests/eval unittest` if needed).
system-test: ## All measuring tests: unit + API Gherkin + e2e + live retrieval + live generation
	$(MAKE) unittest
	$(MAKE) api-test
	$(MAKE) e2e
	$(MAKE) eval-live
	$(MAKE) eval-live-generation

api-test: ## Live HTTP Gherkin (tests/api; stack up + ops bootstrap done)
	$(MAKE) -C $(ROOT)/tests/api run

test-api: api-test

license: licenses-check ## SBOM for all projects + merge + Grant policy gate
licenses: license

eval-live: ## Investigation retrieval IR (live stack, no judge LLM)
	$(MAKE) -C $(ROOT)/tests/eval run-retrieval-suite

eval-live-generation: ## Investigation DeepEval generation gate (slow; live stack)
	$(MAKE) -C $(ROOT)/tests/eval run-generation-suite

e2e: ## Playwright BDD UI — smoke then regression (stack up + ops bootstrap done)
	$(MAKE) -C $(ROOT)/tests/e2e run
