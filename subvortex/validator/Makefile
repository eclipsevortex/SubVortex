# =====================
# Config
# =====================

# Actions per component
ACTIONS := major minor patch alpha rc version clean prerelease release

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

patch:
	@python3 $(VERSION_SCRIPT) patch

minor:
	@python3 $(VERSION_SCRIPT) minor

major:
	@python3 $(VERSION_SCRIPT) major

alpha:
	@python3 $(VERSION_SCRIPT) alpha

rc:
	@python3 $(VERSION_SCRIPT) rc

version:
	@python3 $(VERSION_SCRIPT) new-prerelease

# =====================
# Declare all targets as .PHONY
# =====================
.PHONY: $(TARGETS)

# =====================
# Optional: help target
# =====================
help:
	@echo "📦 Available targets:"
	@$(foreach t,$(sort $(TARGETS)), echo "  $(t)";)
