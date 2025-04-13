# =====================
# Config
# =====================

# Actions per component
ACTIONS := bump-major bump-minor bump-patch bump-alpha bump-rc clean

# Services per component
SERVICES := neuron

# Get the version script
VERSION_SCRIPT = ../../scripts/cicd/cicd_bump_version.py

# =====================
# Reusable macro
# =====================
define make_component
	@echo "🔧 Running [$(2)] on subvortex/$(1)..."
	@$(MAKE) -C $(1) $(2)
	@echo "✅ Done with [$(2)] on subvortex/$(1)"
endef

# =====================
# Dynamic rule generation
# =====================

# Initialize phony targets
TARGETS :=

# Generate 3-part rules: <action>-<service>
$(foreach action,$(ACTIONS),\
	$(foreach service,$(SERVICES),\
		$(eval target := $(action)-$(service)) \
		$(eval $(target): ; $(call make_component,$(service),$(action))) \
		$(eval TARGETS += $(target)) \
	)\
)

bump-patch:
	@python3 $(VERSION_SCRIPT) patch

bump-minor:
	@python3 $(VERSION_SCRIPT) minor

bump-major:
	@python3 $(VERSION_SCRIPT) major

bump-alpha:
	@python3 $(VERSION_SCRIPT) alpha

bump-rc:
	@python3 $(VERSION_SCRIPT) rc

clean:
	rm -rf $(DIST_DIR) *.egg-info **/*.egg-info build/

# =====================
# Declare all targets as .PHONY
# =====================
.PHONY: $(TARGETS)