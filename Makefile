# agentic-rag-eval — monorepo orchestrator
# Python projects own uv.lock; Node projects share root package.json workspaces.

ROOT         := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
UV           ?= uv
UVX          ?= uvx
LICENSES_DIR := $(ROOT)/licenses
REPORTS_DIR  := $(ROOT)/.reports

include $(ROOT)/make/projects.mk
include $(ROOT)/make/licenses.mk

.DEFAULT_GOAL := help

.PHONY: help
help: ## List top-level targets
	@echo "agentic-rag-eval (independent projects)"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-22s %s\n", $$1, $$2}'
	@echo ""
	@echo "Python: $(PYTHON_PROJECTS)"
	@echo "Node:   $(NODE_PROJECTS)"
	@echo "Suites: $(PYTHON_SUITES) $(NODE_SUITES)"
	@echo "Repo map: project.cue (verify: make verify-repo-map)"

# ── Sync / install ───────────────────────────────────────────────────────────

.PHONY: sync install
sync: ## uv sync + npm ci (root workspaces) + OpenAPI export
	@set -e; for p in $(ALL_PYTHON_SYNC); do echo "==> $$p"; $(MAKE) -C $$p sync UV_SYNC_FLAGS=; done
	@echo "==> node workspaces"
	@cd "$(ROOT)" && npm ci
	@$(MAKE) generate-openapi

install: sync ## Alias for sync

.PHONY: sync-frozen
sync-frozen: ## Frozen sync (CI) — requires committed lockfiles
	@set -e; for p in $(ALL_PYTHON_SYNC); do $(MAKE) -C $$p sync; done
	@cd "$(ROOT)" && npm ci

# ── OpenAPI / codegen ─────────────────────────────────────────────────────────

KEYCLOAK_OPENAPI     := $(ROOT)/operations/keycloak/openapi/admin-rest.openapi.yaml
KEYCLOAK_CLIENT_DIR  := $(ROOT)/packages/generated/keycloak-admin-client
KEYCLOAK_CLIENT_CONFIG := $(ROOT)/operations/keycloak/openapi/openapi-python-client.yaml

.PHONY: generate-openapi generate-keycloak-client openapi
generate-openapi: ## Export OpenAPI specs → openapi/
	@mkdir -p $(ROOT)/openapi
	@cd $(ROOT)/services/api && $(UV) run python -c 'import yaml; from pathlib import Path; from agentic_api.main import create_app; s=create_app().openapi(); p=Path("$(ROOT)/openapi"); p.mkdir(exist_ok=True); p.joinpath("api.yaml").write_text(yaml.dump(s, sort_keys=False, allow_unicode=True, default_flow_style=False), encoding="utf-8"); print("Wrote openapi/api.yaml")'
	@cd $(ROOT)/services/chat && $(UV) run python -c 'import yaml; from pathlib import Path; from agentic_chat.main import create_app; s=create_app().openapi(); p=Path("$(ROOT)/openapi"); p.mkdir(exist_ok=True); p.joinpath("chat.yaml").write_text(yaml.dump(s, sort_keys=False, allow_unicode=True, default_flow_style=False), encoding="utf-8"); print("Wrote openapi/chat.yaml")'
	@cd $(ROOT)/services/admin && $(UV) run python -c 'import yaml; from pathlib import Path; from agentic_admin.main import create_app; s=create_app().openapi(); p=Path("$(ROOT)/openapi"); p.mkdir(exist_ok=True); p.joinpath("admin.yaml").write_text(yaml.dump(s, sort_keys=False, allow_unicode=True, default_flow_style=False), encoding="utf-8"); print("Wrote openapi/admin.yaml")'

generate-keycloak-client: ## Keycloak Admin OpenAPI → packages/generated/
	@test -f "$(KEYCLOAK_OPENAPI)" || (echo "Missing $(KEYCLOAK_OPENAPI)" >&2; exit 1)
	@mkdir -p "$(ROOT)/packages/generated"
	@rm -rf "$(KEYCLOAK_CLIENT_DIR)"
	$(UVX) openapi-python-client generate \
		--path "$(KEYCLOAK_OPENAPI)" \
		--config "$(KEYCLOAK_CLIENT_CONFIG)" \
		--meta uv \
		--output-path "$(KEYCLOAK_CLIENT_DIR)" \
		--overwrite \
		--no-fail-on-warning

openapi: generate-openapi

# ── Database ───────────────────────────────────────────────────────────────────

.PHONY: db-migrate db-revision
db-migrate: ## Alembic upgrade head (packages/shared)
	cd $(ROOT)/packages/shared && $(UV) run alembic -c alembic/alembic.ini upgrade head

db-revision: ## Alembic autogenerate (MSG=...)
	cd $(ROOT)/packages/shared && $(UV) run alembic -c alembic/alembic.ini revision --autogenerate -m "$(MSG)"

# ── Repo map (CUE) ─────────────────────────────────────────────────────────────

.PHONY: verify-repo-map sync-projects-mk
verify-repo-map: ## cue vet + folder paths + projects.mk parity (ADR 008)
	"$(ROOT)/scripts/verify_repo_map.sh"

sync-projects-mk: ## Regenerate make/projects.mk lists from project.cue
	cue export project.cue -e projectsMk --out text > "$(ROOT)/make/projects.mk"
	@echo "Wrote make/projects.mk"
	@$(MAKE) verify-repo-map

# ── Quality ────────────────────────────────────────────────────────────────────

.PHONY: test test-unit test-unit-coverage test-coverage lint format hooks
test: test-unit ## All tests

test-unit: ## Unit tests (libs, services, UI)
	@set -e; for p in $(PYTHON_PROJECTS); do echo "==> $$p unit-test"; $(MAKE) -C $$p unit-test; done
	@set -e; for p in $(NODE_PROJECTS); do echo "==> $$p unit-test"; $(MAKE) -C $$p unit-test; done

test-unit-coverage: ## Unit tests + per-project coverage
	@set -e; for p in $(PYTHON_LIBS) $(PYTHON_SERVICES); do echo "==> $$p unit-test-coverage"; $(MAKE) -C $$p unit-test-coverage; done
	@$(MAKE) coverage-combine

test-coverage: test-unit-coverage ## Alias

coverage-combine: ## Combine per-project .coverage → .reports/coverage/combined/ (non-gating)
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

format: ## Auto-format Python (libs, services, suites)
	@set -e; for p in $(PYTHON_PROJECTS) $(PYTHON_SUITES); do $(MAKE) -C $$p format; done

hooks: ## Install pre-commit
	$(UVX) pre-commit install

.PHONY: eval eval-live eval-live-generation e2e test-api
eval: ## Offline eval checks (dataset + metrics)
	$(MAKE) -C tests/eval run

eval-live: ## Retrieval IR gate (live stack, no judge LLM)
	$(MAKE) -C tests/eval run-live

eval-live-generation: ## DeepEval generation gate (slow; live stack)
	$(MAKE) -C tests/eval run-live-generation

e2e: ## Playwright BDD UI (needs make up-ui; not in default CI)
	$(MAKE) -C tests/e2e run

test-api: ## Playwright BDD HTTP (needs make up; not in default CI)
	$(MAKE) -C tests/api run

.PHONY: resources
resources: ## Download demo PDFs into resources/ (not committed)
	@chmod +x $(ROOT)/scripts/fetch-resources.sh
	$(ROOT)/scripts/fetch-resources.sh

# ── SBOM / license policy ──────────────────────────────────────────────────────

.PHONY: licenses
licenses: licenses-check ## SBOM for all projects + merge + Grant policy gate

# ── Docker Compose ─────────────────────────────────────────────────────────────

.PHONY: build up up-ui up-auth down index ops-bootstrap
build: ## docker compose build
	docker compose --profile auth --profile ui build

up: ## Backend stack
	docker compose up -d postgres redis minio qdrant litellm ops indexing api chat admin

up-ui: ## Backend + UI (no Keycloak)
	AUTH_MODE=none INTERNAL_SERVICE_KEY=dev-internal-service-key-change-me \
		VITE_AUTH_ENABLED=false docker compose --profile ui up -d --build

up-auth: ## Full stack + Keycloak + Traefik + UI
	AUTH_MODE=jwt VITE_AUTH_ENABLED=true VITE_KEYCLOAK_URL=$${VITE_KEYCLOAK_URL:-http://localhost} \
		docker compose --profile auth --profile ui up -d --build

down: ## Stop containers
	docker compose down

ops-bootstrap: ## Run migrate + MinIO bootstrap container
	docker compose run --rm ops

index: ## Trigger reindex
	curl -X POST http://localhost:8000/v1/admin/index \
		-H "X-API-Key: $${API_KEY:-dev-admin-key-change-me}"

.PHONY: dev dev-api dev-chat dev-indexing dev-admin dev-ui dev-admin-ui
dev-api:      ; $(MAKE) -C services/api dev
dev-chat:     ; $(MAKE) -C services/chat dev
dev-admin:    ; $(MAKE) -C services/admin dev
dev-indexing: ; $(MAKE) -C services/indexing dev
dev-ui:       ; $(MAKE) -C frontend/app-ui dev
dev-admin-ui: ; $(MAKE) -C frontend/admin-app-ui dev

.PHONY: gh-labels
gh-labels: ## GitHub labels (needs gh auth)
	gh label create bug --color d73a4a --description "Something is broken" --force
	gh label create enhancement --color a2eeef --description "New feature or improvement" --force
	gh label create chore --color fef2c0 --description "Maintenance, deps, tooling" --force
	gh label create documentation --color 0075ca --description "Docs only" --force
	gh label create test --color d4c5f9 --description "Tests or eval suite" --force
