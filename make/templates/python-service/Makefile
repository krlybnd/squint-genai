ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..
PROJECT_NAME := {{PROJECT_NAME}}
PROJECT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
include $(ROOT)/make/report.mk
include $(ROOT)/make/python.mk

PACKAGE := {{PACKAGE}}

.PHONY: dev

dev: ## Start service locally
	@echo "Override dev target in project Makefile"
