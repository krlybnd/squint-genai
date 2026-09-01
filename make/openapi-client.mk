# $(call openapi-python-client,<spec.yaml>,<config.yaml>,<output-dir>)
define openapi-python-client
test -f "$(1)" || { echo "Missing $(1)" >&2; exit 1; }; \
$(UVX) openapi-python-client generate \
	--path "$(1)" \
	--config "$(2)" \
	--meta uv \
	--output-path "$(3)" \
	--overwrite \
	--no-fail-on-warning
endef
