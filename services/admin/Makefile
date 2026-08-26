ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
PROJECT_NAME := admin
PROJECT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
include $(ROOT)/make/report.mk
include $(ROOT)/make/python.mk

PACKAGE := agentic-admin
PORT    ?= 8003

.PHONY: dev

dev: sync ## Start admin service (uvicorn reload on :8003)
	$(UV) run uvicorn agentic_admin.main:create_app --factory --reload --host 0.0.0.0 --port $(PORT)
