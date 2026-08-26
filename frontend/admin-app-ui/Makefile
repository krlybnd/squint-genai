ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
PROJECT_NAME := admin-app-ui
NPM_WORKSPACE := @are/admin-app-ui
PROJECT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PROJECT_STACK := node
include $(ROOT)/make/report.mk
include $(ROOT)/make/node.mk

.PHONY: dev
dev: install ## Vite dev server on :5174
	cd "$(ROOT)" && $(NPM) run dev -w $(NPM_WORKSPACE)
