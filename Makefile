# agentic-rag-eval — monorepo orchestrator
# Python projects own uv.lock; Node projects share root package.json workspaces.

ROOT         := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
UV           ?= uv
UVX          ?= uvx
LICENSES_DIR := $(ROOT)/licenses
REPORTS_DIR  := $(ROOT)/.reports

include $(ROOT)/make/projects.mk
include $(ROOT)/make/licenses.mk
include $(ROOT)/make/openapi-client.mk
include $(ROOT)/tools/ops/Makefile
include $(ROOT)/tools/qa/Makefile

.DEFAULT_GOAL := help

.PHONY: help
help: ## List top-level targets
	@echo "agentic-rag-eval (independent projects)"
	@echo ""
	@grep -hE '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-22s %s\n", $$1, $$2}'
	@echo ""
	@echo "Python: $(PYTHON_PROJECTS)"
	@echo "Node:   $(NODE_PROJECTS)"
	@echo "Suites: $(PYTHON_SUITES) $(NODE_SUITES)"
	@echo "Repo map: project.cue (verify: make verify-repo-map)"
	@echo "Stack:    tools/ops/README.md (docker compose; Make is not the host entry)"

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
API_CLIENT_DIR       := $(ROOT)/packages/generated/agentic-api-client
CHAT_CLIENT_DIR      := $(ROOT)/packages/generated/agentic-chat-client
API_CLIENT_CONFIG    := $(ROOT)/openapi/python-client-api.yaml
CHAT_CLIENT_CONFIG   := $(ROOT)/openapi/python-client-chat.yaml

.PHONY: generate-openapi generate-openapi-clients openapi
generate-openapi: ## Export OpenAPI specs → openapi/
	@mkdir -p $(ROOT)/openapi
	@cd $(ROOT)/services/api && $(UV) run python -c 'import yaml; from pathlib import Path; from agentic_api.main import create_app; s=create_app().openapi(); p=Path("$(ROOT)/openapi"); p.mkdir(exist_ok=True); p.joinpath("api.yaml").write_text(yaml.dump(s, sort_keys=False, allow_unicode=True, default_flow_style=False), encoding="utf-8"); print("Wrote openapi/api.yaml")'
	@cd $(ROOT)/services/chat && $(UV) run python -c 'import yaml; from pathlib import Path; from agentic_chat.main import create_app; s=create_app().openapi(); p=Path("$(ROOT)/openapi"); p.mkdir(exist_ok=True); p.joinpath("chat.yaml").write_text(yaml.dump(s, sort_keys=False, allow_unicode=True, default_flow_style=False), encoding="utf-8"); print("Wrote openapi/chat.yaml")'
	@cd $(ROOT)/services/admin && $(UV) run python -c 'import yaml; from pathlib import Path; from agentic_admin.main import create_app; s=create_app().openapi(); p=Path("$(ROOT)/openapi"); p.mkdir(exist_ok=True); p.joinpath("admin.yaml").write_text(yaml.dump(s, sort_keys=False, allow_unicode=True, default_flow_style=False), encoding="utf-8"); print("Wrote openapi/admin.yaml")'

generate-openapi-clients: ## api.yaml + chat.yaml + Keycloak Admin → packages/generated/
	@mkdir -p "$(ROOT)/packages/generated"
	@rm -rf "$(API_CLIENT_DIR)" "$(CHAT_CLIENT_DIR)" "$(KEYCLOAK_CLIENT_DIR)"
	$(call openapi-python-client,$(ROOT)/openapi/api.yaml,$(API_CLIENT_CONFIG),$(API_CLIENT_DIR))
	$(call openapi-python-client,$(ROOT)/openapi/chat.yaml,$(CHAT_CLIENT_CONFIG),$(CHAT_CLIENT_DIR))
	$(call openapi-python-client,$(KEYCLOAK_OPENAPI),$(KEYCLOAK_CLIENT_CONFIG),$(KEYCLOAK_CLIENT_DIR))

openapi: generate-openapi

# ── Database ───────────────────────────────────────────────────────────────────

.PHONY: db-migrate db-revision
db-migrate: migrate ## Alembic upgrade head (alias)

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

.PHONY: gh-labels
gh-labels: ## GitHub labels (needs gh auth)
	gh label create bug --color d73a4a --description "Something is broken" --force
	gh label create enhancement --color a2eeef --description "New feature or improvement" --force
	gh label create chore --color fef2c0 --description "Maintenance, deps, tooling" --force
	gh label create documentation --color 0075ca --description "Docs only" --force
	gh label create test --color d4c5f9 --description "Tests or eval suite" --force
