# Operator recipes — no Docker. Host or `docker compose exec ops make <target>`.
# Demo and live tests share the same Keycloak personas (`add-users`).

OPS_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
ROOT ?= $(abspath $(OPS_DIR)/../..)

API_BASE ?= http://localhost:8000
KEYCLOAK_URL ?= http://localhost:8080

ADD_USER_SCRIPT := $(ROOT)/scripts/keycloak/add-user.sh
MINIO_SETUP := $(ROOT)/scripts/minio/setup.sh
MINIO_TEARDOWN := $(ROOT)/scripts/minio/teardown.sh
POSTGRES_MIGRATE := $(ROOT)/scripts/postgres/migrate.sh
POSTGRES_TEARDOWN := $(ROOT)/scripts/postgres/teardown.sh
QDRANT_TEARDOWN := $(ROOT)/scripts/qdrant/teardown.sh
REDIS_TEARDOWN := $(ROOT)/scripts/redis/teardown.sh
API_INDEX := $(ROOT)/scripts/api/index.sh

# username|password|email|firstName|lastName|active_tenant|orgs|roles
# roles: tenant=role+role;tenant=role
define DEMO_USERS
admin|admin|admin@local|Admin|User|tenant-a|tenant-a,tenant-b|tenant-a=admin+write+read;tenant-b=admin+write+read
alice@tenant-a.local|alice|alice@tenant-a.local|Alice|TenantA|tenant-a|tenant-a|tenant-a=read+write
bob@tenant-b.local|bob|bob@tenant-b.local|Bob|TenantB|tenant-b|tenant-b|tenant-b=read
writer@tenant-a.local|writer|writer@tenant-a.local|Writer|TenantA|tenant-a|tenant-a|tenant-a=read+write
reader@tenant-a.local|reader|reader@tenant-a.local|Reader|TenantA|tenant-a|tenant-a|tenant-a=read
endef
export DEMO_USERS

# filename|url
define DEMO_RESOURCES
attention-is-all-you-need.pdf|https://arxiv.org/pdf/1706.03762
rag-lewis-2020.pdf|https://arxiv.org/pdf/2005.11401
us-constitution.pdf|https://constitution.congress.gov/static/files/Literal_Print_of_Constitution_MCT_1.9.26.pdf
nasa-fy2025-mission-fact-sheets.pdf|https://www.nasa.gov/wp-content/uploads/2024/03/nasa-fiscal-year-2025-mission-fact-sheets.pdf
nist-ai-rmf-1.0.pdf|https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf
endef
export DEMO_RESOURCES

.PHONY: resources add-user add-users setup-minio index migrate initialization bootstrap teardown restart

resources: ## Download demo PDFs into resources/
	$(ROOT)/scripts/fetch-resources.sh

# USERNAME= PASSWORD= [EMAIL=] [FIRST_NAME=] [LAST_NAME=] [TENANT=] [ORGS=] [ROLES=]
# ROLES: tenant-a=read+write;tenant-b=read
add-user: ## Add or update one Keycloak user (USERNAME + PASSWORD)
	@test -n "$(USERNAME)" || (echo "USERNAME is required" >&2; exit 1)
	@test -n "$(PASSWORD)" || (echo "PASSWORD is required" >&2; exit 1)
	KEYCLOAK_URL="$(KEYCLOAK_URL)" "$(ADD_USER_SCRIPT)" --username "$(USERNAME)" --password "$(PASSWORD)" \
		$(if $(EMAIL),--email "$(EMAIL)") \
		$(if $(FIRST_NAME),--first-name "$(FIRST_NAME)") \
		$(if $(LAST_NAME),--last-name "$(LAST_NAME)") \
		$(if $(TENANT),--tenant "$(TENANT)") \
		$(if $(ORGS),--orgs "$(ORGS)") \
		$(if $(ROLES),--roles "$(ROLES)")

add-users: ## Seed demo/test Keycloak users (same personas for demo and live tests)
	KEYCLOAK_URL="$(KEYCLOAK_URL)" "$(ADD_USER_SCRIPT)" --seed

setup-minio: ## Ensure MinIO bucket + CORS
	"$(MINIO_SETUP)"

migrate: ## Alembic upgrade head
	"$(POSTGRES_MIGRATE)"

initialization: setup-minio resources ## Infra: MinIO bucket + CORS, demo PDFs

bootstrap: migrate ## After apps are up: migrate, seed users, reindex
	WAIT_TIMEOUT=60 $(MAKE) add-users
	$(MAKE) index

teardown: ## Wipe app data (Postgres, MinIO, Qdrant, Redis)
	"$(MINIO_TEARDOWN)"
	"$(POSTGRES_TEARDOWN)"
	"$(QDRANT_TEARDOWN)"
	"$(REDIS_TEARDOWN)"

restart: ## teardown, initialization, then bootstrap
	$(MAKE) teardown
	$(MAKE) initialization
	$(MAKE) bootstrap

index: ## Trigger reindex (running api)
	API_BASE="$(API_BASE)" "$(API_INDEX)"
