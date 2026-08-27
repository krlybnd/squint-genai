// Squint repo map — machine-readable structure for agents, onboarding, and drift checks.
// Canonical source for monorepo project lists (see build.*). Human "why" stays in docs/adr/.
// Verify: make verify-repo-map | Sync project lists: make sync-projects-mk

package project

import "strings"

#Stack: "python" | "node" | "infra" | "docs" | "tests" | "tooling" | "meta"

#Folder: {
	path:     string & =~"^[^/].*"
	purpose:  string
	stack:    #Stack
	phase:    1 | 2
	adr?:     [...string]
	contains?: [...string]
	mustNot?: [...string]
	related?: [...string]
}

project: {
	name:        "Squint"
	repository:  "agentic-rag-eval"
	description: "Eval-driven agentic RAG reference architecture — verifiable citations, LangGraph chat, Celery indexing."
	phase:       1
	docs:        "docs/README.md"
	architecture: "docs/architecture.md"
}

// Monorepo fan-out lists — keep in sync with make/projects.mk via make sync-projects-mk.
build: {
	pythonLibs:     ["packages/shared"]
	pythonServices: ["services/admin", "services/api", "services/chat", "services/indexing"]
	pythonSuites:   ["tests/eval"]
	nodeLibs:       ["packages/ui-core"]
	nodeApps:       ["frontend/app-ui", "frontend/admin-app-ui"]
	nodeSuites:     ["tests/e2e", "tests/api"]
	pythonReportNames: ["shared", "admin", "api", "chat", "indexing"]
}

// Rendered GNU Make include — regenerate with: make sync-projects-mk
projectsMk: """
	# Single source of truth for all projects in the monorepo.
	# Canonical lists live in ../project.cue (build.*) — ADR 008.
	# Regenerate: make sync-projects-mk | Verify: make verify-repo-map

	PYTHON_LIBS         := \(strings.Join(build.pythonLibs, " "))
	PYTHON_SERVICES     := \(strings.Join(build.pythonServices, " "))
	PYTHON_SUITES       := \(strings.Join(build.pythonSuites, " "))
	NODE_LIBS           := \(strings.Join(build.nodeLibs, " "))
	NODE_APPS           := \(strings.Join(build.nodeApps, " "))
	NODE_SUITES         := \(strings.Join(build.nodeSuites, " "))
	PYTHON_REPORT_NAMES := \(strings.Join(build.pythonReportNames, " "))

	PYTHON_PROJECTS := $(PYTHON_LIBS) $(PYTHON_SERVICES)

	NODE_PROJECTS   := $(NODE_LIBS) $(NODE_APPS)

	# Sync/install fan-out (includes test runners)
	ALL_PYTHON_SYNC := $(PYTHON_PROJECTS) $(PYTHON_SUITES)
	ALL_NODE_SYNC   := $(NODE_PROJECTS) $(NODE_SUITES)

	# Short names for report paths (.reports/python/<name>/, .reports/node/<name>/)
	"""

folders: {
	"packages/shared": #Folder & {
		path:    "packages/shared"
		stack:   "python"
		phase:   1
		adr:     ["001", "004", "006"]
		purpose: """
			Shared Python library: domain logic (retrieval, persistence entities/repos),
			auth/RBAC, backend i18n catalogs, compliance hooks, infra clients (Postgres,
			Redis, MinIO, Qdrant), LLM/embedding integrations, FastAPI bootstrap helpers.
			Consumed by all Python services — not a deployable HTTP service.
			"""
		contains: ["src/agentic_shared/domains/", "src/agentic_shared/core/", "src/agentic_shared/infrastructure/", "tests/unittest/", "alembic/"]
		mustNot:  ["product REST routers", "Celery task entrypoints", "LangGraph chat graph"]
		related:  ["services/api", "services/chat", "services/admin", "services/indexing"]
	}

	"packages/ui-core": #Folder & {
		path:    "packages/ui-core"
		stack:   "node"
		phase:   1
		adr:     ["005"]
		purpose: """
			Shared React platform UI: AppShell, auth/i18n/theme bootstrap, Vite helpers,
			form primitives, OpenAPI client generation script. Product screens stay in apps.
			"""
		contains: ["src/app/", "src/auth/", "src/components/", "src/build/"]
		mustNot:  ["chat-specific screens", "admin CRUD pages"]
		related:  ["frontend/app-ui", "frontend/admin-app-ui"]
	}

	"packages/generated": #Folder & {
		path:    "packages/generated"
		stack:   "python"
		phase:   1
		purpose: "Generated clients (Keycloak Admin OpenAPI). Regenerate via make generate-keycloak-client — do not hand-edit."
		mustNot: ["manual feature code"]
	}

	"services/api": #Folder & {
		path:    "services/api"
		stack:   "python"
		phase:   1
		purpose: """
			REST API: document upload/metadata, index jobs, retrieval search, chunk annotations.
			Vertical slices under modules/. Indexes via Celery enqueue only — never sync indexing.
			"""
		contains: ["src/agentic_api/modules/", "tests/unittest/"]
		mustNot:  ["LangGraph agent graph", "semantic chunking in request path"]
		related:  ["services/indexing", "packages/shared", "openapi/api.yaml"]
	}

	"services/chat": #Folder & {
		path:    "services/chat"
		stack:   "python"
		phase:   1
		adr:     ["001", "006"]
		purpose: """
			Stateful chat service: LangGraph workflow (plan → guard → rewrite → retrieve → generate),
			Postgres checkpointing, SSE streaming. Retrieval runs in-process from shared domain lib.
			"""
		contains: ["src/agentic_chat/core/graph/", "src/agentic_chat/core/nodes/", "src/agentic_chat/modules/chat/"]
		mustNot:  ["document upload REST", "Celery PDF indexing pipeline"]
		related:  ["packages/shared", "openapi/chat.yaml"]
	}

	"services/indexing": #Folder & {
		path:    "services/indexing"
		stack:   "python"
		phase:   1
		purpose: """
			Celery worker service: PDF download from MinIO, semantic chunking, embedding, Qdrant upsert.
			No HTTP product API — triggered by api job queue only.
			"""
		contains: ["src/agentic_indexing/modules/", "tests/unittest/"]
		mustNot:  ["FastAPI routers for clients", "sync indexing from api handlers"]
		related:  ["services/api", "packages/shared"]
	}

	"services/admin": #Folder & {
		path:    "services/admin"
		stack:   "python"
		phase:   1
		purpose: "Keycloak Organizations admin REST: tenants and users/memberships for multitenancy demo."
		contains: ["src/agentic_admin/modules/"]
		related:  ["openapi/admin.yaml", "frontend/admin-app-ui"]
	}

	"frontend/app-ui": #Folder & {
		path:    "frontend/app-ui"
		stack:   "node"
		phase:   1
		adr:     ["005"]
		purpose: "Main product UI: documents sidebar, chat sessions, SSE streaming, citations. Composes @are/ui-core AppShell."
		related: ["packages/ui-core", "services/chat", "services/api"]
	}

	"frontend/admin-app-ui": #Folder & {
		path:    "frontend/admin-app-ui"
		stack:   "node"
		phase:   1
		adr:     ["005"]
		purpose: "Admin UI: tenant/user CRUD. Mounted at /admin via Traefik when auth+ui profiles enabled."
		related: ["services/admin", "packages/ui-core"]
	}

	"tests/api": #Folder & {
		path:    "tests/api"
		stack:   "tests"
		phase:   1
		adr:     ["004", "007"]
		purpose: """
			Live-stack HTTP acceptance: Playwright-BDD, steps use only OpenAPI-generated clients.
			Requires make up. Not in default CI (ADR 007).
			"""
		mustNot: ["pytest integration suites under services/", "importing FastAPI apps in service tests"]
		related: ["openapi/", ".reports/api"]
	}

	"tests/e2e": #Folder & {
		path:    "tests/e2e"
		stack:   "tests"
		phase:   1
		adr:     ["007"]
		purpose: "Browser UI journeys (Playwright + Gherkin). Manual / on-demand; reports under .reports/e2e/."
		related: ["frontend/app-ui", "frontend/admin-app-ui"]
	}

	"tests/eval": #Folder & {
		path:    "tests/eval"
		stack:   "tests"
		phase:   1
		adr:     ["002", "007"]
		purpose: """
			DeepEval generation (`evaluate()` script, TTY progress bar) plus Pydantic Evals
			retrieval IR. Generic core (goldendata, judge_model, HostStack) plus
			modules/retrieval and modules/generation. Live stack wiring is tests/suit
			(SutSettings, EVAL_SUT_*). Own .env / .env.example (not repo-root).
			make eval-live / eval-live-generation against running stack. Not in CI.
			Committed snapshots: reports/eval/.
			"""
		contains: ["src/agentic_eval/core/", "src/agentic_eval/modules/", "tests/unittest/", "tests/suit/", "dataset.json", ".env.example"]
		mustNot: ["hand-rolled .env parsers", "eval config on LLMSettings", "os.environ host rewrites", "src importing tests/", "DeepEval SDK calls from modules without the judge adapter"]
		related: ["resources/", "services/chat", "reports"]
	}

	"openapi": #Folder & {
		path:    "openapi"
		stack:   "meta"
		phase:   1
		adr:     ["004"]
		purpose: """
			Committed OpenAPI YAML (api.yaml, chat.yaml, admin.yaml). Source for UI
			client generation and tests/api contract. YAML only — regenerate with
			make generate-openapi.
			"""
		mustNot: ["duplicate JSON specs (api.json / chat.json / admin.json)"]
		related: ["make generate-openapi", "tests/api"]
	}

	"operations": #Folder & {
		path:    "operations"
		stack:   "infra"
		phase:   1
		purpose: "Infra-side configs: Keycloak realm, LiteLLM, Postgres/Redis/MinIO/Qdrant/Traefik snippets for docker-compose."
		related: ["docker-compose.yml", "tools/ops/bootstrap"]
	}

	"tools/ops": #Folder & {
		path:    "tools/ops"
		stack:   "tooling"
		phase:   1
		purpose: "Ops/bootstrap scripts (migrate, MinIO CORS, bucket setup). Dagger test profiles optional."
		related: ["operations/", "make ops-bootstrap"]
	}

	"make": #Folder & {
		path:    "make"
		stack:   "tooling"
		phase:   1
		purpose: "Shared Makefile templates (python.mk, node.mk, report.mk) and project fan-out lists (projects.mk)."
		related: ["project.cue", "Makefile"]
	}

	"docs": #Folder & {
		path:    "docs"
		stack:   "docs"
		phase:   1
		purpose: "Human architecture docs, compliance readiness, ADRs. Start at docs/README.md."
		contains: ["adr/", "architecture.md", "project-overview.md"]
	}

	"docs/adr": #Folder & {
		path:    "docs/adr"
		stack:   "docs"
		phase:   1
		purpose: "Architecture Decision Records — why, not where. Repo structure lives in project.cue (ADR 008)."
	}

	".cursor/rules": #Folder & {
		path:    ".cursor/rules"
		stack:   "meta"
		phase:   1
		purpose: "Cursor agent conventions: scope, backend/frontend/testing rules, repo-map drift policy."
		related: ["project.cue", "docs/adr"]
	}

	"licenses": #Folder & {
		path:    "licenses"
		stack:   "meta"
		phase:   1
		purpose: "Per-project CycloneDX SBOM fragments and merged bom.cdx.json for Grant license policy."
		related: ["make licenses", ".grant.yaml"]
	}

	"reports": #Folder & {
		path:    "reports"
		stack:   "docs"
		phase:   1
		adr:     ["007"]
		purpose: """
			Committed live-eval snapshots under reports/eval/ (retrieval IR + DeepEval
			generation). Generated locally, not CI. Distinct from gitignored .reports/.
			"""
		contains: ["eval/"]
		related: ["tests/eval"]
	}

	".reports": #Folder & {
		path:    ".reports"
		stack:   "meta"
		phase:   1
		purpose: """
			Generated CI/local reports (gitignored): .reports/python/<name>/, .reports/node/<name>/,
			.reports/coverage/combined/, .reports/licenses/, .reports/api/, .reports/e2e/.
			"""
		related: ["make/report.mk"]
	}

	"resources": #Folder & {
		path:    "resources"
		stack:   "docs"
		phase:   1
		purpose: "Demo PDFs for indexing/eval goldens. Fetched via make resources — not always committed."
		related: ["tests/eval", "scripts/fetch-resources.sh"]
	}

	".github/workflows": #Folder & {
		path:    ".github/workflows"
		stack:   "meta"
		phase:   1
		purpose: "CI: per-project lint/unit/coverage, license policy, coverage combine. No live stack (ADR 007)."
		related: ["make/projects.mk", "project.cue"]
	}
}

// Folders that may be absent locally (generated / optional).
optionalFolderPaths: {
	".reports":           true
	"licenses":           true
	"packages/generated": true
}

requiredFolderPaths: [
	for k, _ in folders if optionalFolderPaths[k] == _|_ {k},
]

requiredFolderPathsText: strings.Join(requiredFolderPaths, "\n")
