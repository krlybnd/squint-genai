ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
PROJECT_NAME := api
PROJECT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
include $(ROOT)/make/report.mk
include $(ROOT)/make/python.mk

PACKAGE := agentic-api
PORT    ?= 8000

.PHONY: dev

dev: sync ## Start API (uvicorn reload on :8000)
	$(UV) run uvicorn agentic_api.main:create_app --factory --reload --host 0.0.0.0 --port $(PORT)
