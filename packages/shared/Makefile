ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
PROJECT_NAME := shared
PROJECT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
include $(ROOT)/make/report.mk
include $(ROOT)/make/python.mk

PACKAGE := agentic-shared

.PHONY: dev

dev: ## Library — use a service Makefile for dev server
	@echo "$(PACKAGE): run \`make -C services/api dev\` or another service."
