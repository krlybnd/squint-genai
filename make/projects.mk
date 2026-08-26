# Single source of truth for all projects in the monorepo.
# Canonical lists live in ../project.cue (build.*) — ADR 008.
# Regenerate: make sync-projects-mk | Verify: make verify-repo-map

PYTHON_LIBS         := packages/shared
PYTHON_SERVICES     := services/admin services/api services/chat services/indexing
PYTHON_SUITES       := tests/eval
NODE_LIBS           := packages/ui-core
NODE_APPS           := frontend/app-ui frontend/admin-app-ui
NODE_SUITES         := tests/e2e tests/api
PYTHON_REPORT_NAMES := shared admin api chat indexing

PYTHON_PROJECTS := $(PYTHON_LIBS) $(PYTHON_SERVICES)

NODE_PROJECTS   := $(NODE_LIBS) $(NODE_APPS)

# Sync/install fan-out (includes test runners)
ALL_PYTHON_SYNC := $(PYTHON_PROJECTS) $(PYTHON_SUITES)
ALL_NODE_SYNC   := $(NODE_PROJECTS) $(NODE_SUITES)

# Short names for report paths (.reports/python/<name>/, .reports/node/<name>/)
