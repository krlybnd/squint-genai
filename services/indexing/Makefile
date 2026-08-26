ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
PROJECT_NAME := indexing
PROJECT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
include $(ROOT)/make/report.mk
include $(ROOT)/make/python.mk

PACKAGE := agentic-indexing

.PHONY: dev

dev: sync ## Start Celery indexing worker
	$(UV) run celery -A agentic_indexing.main:celery_app worker --loglevel=info --concurrency=2

integration-test:: _report-dirs-integration
	$(call write-empty-junit,integration,$(INTEGRATION_TEST_REPORT))
	@echo "$(PROJECT_NAME): no integration tests"
