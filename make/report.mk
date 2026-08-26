# Report paths and JUnit helpers. Requires ROOT and PROJECT_NAME.
#
# Layout under $(ROOT)/.reports/:
#   python/<name>/     unit-test.xml, .coverage, coverage/, sbom.cdx.json
#   node/<name>/       unit-test.xml, sbom.cdx.json
#   coverage/combined/ merged Python HTML (root Makefile: coverage-combine)
#   licenses/bom.cdx.json
#   api/, e2e/         Playwright suites (configured in tests/*)

LICENSES_DIR ?= $(ROOT)/licenses
REPORTS_DIR  ?= $(ROOT)/.reports

# Node Makefiles set PROJECT_STACK := node before including this file.
PROJECT_STACK      ?= python
PROJECT_REPORT_DIR ?= $(REPORTS_DIR)/$(PROJECT_STACK)/$(PROJECT_NAME)

UNIT_TEST_REPORT        ?= $(PROJECT_REPORT_DIR)/unit-test.xml
INTEGRATION_TEST_REPORT ?= $(PROJECT_REPORT_DIR)/integration-test.xml
SBOM_REPORT             ?= $(PROJECT_REPORT_DIR)/sbom.cdx.json
COVERAGE_DATA_FILE      ?= $(PROJECT_REPORT_DIR)/.coverage
COVERAGE_HTML_DIR       ?= $(PROJECT_REPORT_DIR)/coverage

.PHONY: _report-dirs-unit _report-dirs-integration _report-dirs-sbom _report-dirs-coverage

_report-dirs-unit:
	@mkdir -p $(dir $(UNIT_TEST_REPORT))

_report-dirs-integration:
	@mkdir -p $(dir $(INTEGRATION_TEST_REPORT))

_report-dirs-sbom:
	@mkdir -p $(dir $(SBOM_REPORT))

_report-dirs-coverage:
	@mkdir -p $(COVERAGE_HTML_DIR)

# write-empty-junit <suite-name> <output-path>
define write-empty-junit
	echo '<?xml version="1.0" encoding="utf-8"?><testsuite name="$(1)" tests="0" failures="0" errors="0" skipped="0"/>' > $(2)
endef
