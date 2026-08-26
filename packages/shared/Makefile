ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
PROJECT_NAME := shared
PROJECT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
include $(ROOT)/make/report.mk
include $(ROOT)/make/python.mk

PACKAGE := agentic-shared

.PHONY: dev lint

dev: ## Library — use a service Makefile for dev server
	@echo "$(PACKAGE): run \`make -C services/api dev\` or another service."

lint: ## Ruff check + format + strict mypy (packages/shared)
	$(UV) run ruff check
	$(UV) run ruff format --check
	$(UV) run mypy --config-file $(PROJECT_DIR)/mypy.ini src
	@if grep -RInE --include='*.py' '__getattr__|\bgetattr\(|\bhasattr\(' src; then \
		echo "getattr/hasattr is banned: bind the type instead of duck-typing"; \
		exit 1; \
	fi
