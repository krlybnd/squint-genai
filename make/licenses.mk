# SBOM collection, merge, and license policy gate (Anchore Grant).
# Requires docker for cyclonedx-cli merge and grant check.

GRANT_IMAGE          ?= anchore/grant:latest
CYCLONEDX_CLI_IMAGE  ?= cyclonedx/cyclonedx-cli:latest
GRANT_CONFIG         ?= $(ROOT)/.grant.yaml
LICENSE_BOM          ?= $(LICENSES_DIR)/bom.cdx.json

NODE_REPORT_NAMES    := ui-core app-ui admin-app-ui
LICENSE_REPORT_NAMES := $(PYTHON_REPORT_NAMES) $(NODE_REPORT_NAMES)

.PHONY: licenses-collect licenses-merge licenses-check licenses-list

licenses-collect: ## Per-project CycloneDX SBOM → licenses/*.cdx.json
	@mkdir -p $(LICENSES_DIR)
	@set -e; for p in $(PYTHON_PROJECTS) $(NODE_PROJECTS); do \
		echo "==> $$p licenses"; \
		$(MAKE) -C $$p licenses; \
	done

licenses-merge: licenses-collect ## Merge SBOMs → licenses/bom.cdx.json
	@files=$$(cd $(LICENSES_DIR) && ls *.cdx.json 2>/dev/null | grep -v '^bom\.cdx\.json$$' | sed 's|^|/bom/|' | tr '\n' ' '); \
	if [ -z "$$files" ]; then \
		echo "No SBOM files under $(LICENSES_DIR)" >&2; exit 1; \
	fi; \
	docker run --rm -v $(LICENSES_DIR):/bom $(CYCLONEDX_CLI_IMAGE) merge \
		--input-files $$files \
		--output-file /bom/bom.cdx.json \
		--output-format json --output-version v1_5
	@mkdir -p $(REPORTS_DIR)/licenses
	@cp $(LICENSE_BOM) $(REPORTS_DIR)/licenses/bom.cdx.json
	@echo "Merged SBOM: $(LICENSE_BOM)"

licenses-list: licenses-merge ## List licenses (non-gating, for waivers)
	docker run --rm -v $(ROOT):/work -w /work $(GRANT_IMAGE) \
		list licenses/bom.cdx.json

licenses-check: licenses-merge ## Enforce .grant.yaml policy (non-zero on violation)
	docker run --rm -v $(ROOT):/work -w /work $(GRANT_IMAGE) \
		check -c .grant.yaml licenses/bom.cdx.json
