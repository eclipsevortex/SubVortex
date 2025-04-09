# =====================
# Config
# =====================

# Actions per component
ACTIONS_miner := major minor patch alpha rc version
ACTIONS_validator := major minor patch alpha rc version

# Services per component
SERVICES_miner := neuron
SERVICES_validator := neuron

# All components
COMPONENTS := miner validator

# Get the current branch
CURRENT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

# Get the version script
VERSION_SCRIPT = ./scripts/cicd/cicd_bump_version.py

DIST_DIR = ./dist

# =====================
# Reusable macro
# =====================
define make_component
	@echo "🔧 Running [$(2)] on subvortex/$(1)..."
	@$(MAKE) -C subvortex/$(1) $(2)
	@echo "✅ Done with [$(2)] on subvortex/$(1)"
endef

# =====================
# Dynamic rule generation
# =====================

# Initialize phony targets
TARGETS := ${ACTIONS_miner}

# Generate 3-part rules: <action>-<component>-<service>
$(foreach comp,$(COMPONENTS),\
  $(foreach action,$(ACTIONS_$(comp)),\
    $(foreach service,$(SERVICES_$(comp)),\
      $(eval target := $(action)-$(comp)-$(service)) \
      $(eval $(target): ; $(call make_component,$(comp)/$(service),$(action))) \
      $(eval TARGETS += $(target)) \
    )\
  )\
)

# Generate 2-part rules: <action>-<component> (entire component)
$(foreach comp,$(COMPONENTS),\
  $(foreach action,$(ACTIONS_$(comp)),\
    $(eval target := $(action)-$(comp)) \
    $(eval $(target): ; $(call make_component,$(comp),$(action))) \
    $(eval TARGETS += $(target)) \
  )\
)

# =====================
# Declare all targets as .PHONY
# =====================
TARGETS += clean-miner build-miner clean-validator build-validator tag delete-tag prerelease release
.PHONY: $(TARGETS) help

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

clean-miner:
	@echo "🧹 Cleaning miner build artifacts..." && \
	rm -rf dist/subvortex_miner* build *.egg-info && \
	[ -f pyproject.toml ] && grep -q 'name = "subvortex_miner"' pyproject.toml && rm pyproject.toml || true && \
	echo "✅ Miner clean complete."

build-miner:
	@$(MAKE) clean-miner && \
	echo "📦 Building miner with pyproject-miner.toml..." && \
	cp pyproject-miner.toml pyproject.toml && \
	python3 -m build --no-isolation --sdist --wheel -o dist && \
	rm pyproject.toml && \
	\
	for f in dist/subvortex-*; do \
		mv "$$f" "$${f/subvortex-/subvortex_miner-}"; \
	done && \
	echo "✅ Miner build done."

clean-validator:
	@echo "🧹 Cleaning validator build artifacts..." && \
	rm -rf dist/subvortex_validator* build *.egg-info && \
	[ -f pyproject.toml ] && grep -q 'name = "subvortex_validator"' pyproject.toml && rm pyproject.toml || true && \
	echo "✅ Validator clean complete."

build-validator:
	@$(MAKE) clean-validator && \
	echo "📦 Building validator with pyproject-validator.toml..." && \
	cp pyproject-validator.toml pyproject.toml && \
	python3 -m build --no-isolation --sdist --wheel -o dist && \
	rm pyproject.toml && \
	\
	for f in dist/subvortex-*; do \
		mv "$$f" "$${f/subvortex-/subvortex_validator-}"; \
	done && \
	echo "✅ Validator build done."

build: build-miner build-validator

tag:
	@VERSION=$$(cat VERSION); \
	TAG=v$$VERSION; \
	echo "🏷️  Creating tag $$TAG on branch $(CURRENT_BRANCH)..."; \
	git tag $$TAG && git push origin $$TAG;

delete-tag:
ifndef TAG
	$(error ❌ Please specify the tag to delete: make delete-tag TAG=vX.Y.Z)
endif
	@echo "🔧 Deleting local tag $(TAG)..."
	@git tag -d $(TAG) || echo "⚠️  Local tag $(TAG) does not exist"
	@echo "🌐 Deleting remote tag $(TAG)..."
	@git push origin :refs/tags/$(TAG) || echo "⚠️  Remote tag $(TAG) may not exist"

prerelease:
	@VERSION=$$(cat VERSION); \
	TAG=v$$VERSION; \
	echo "🏷️  Creating prerelease tag $$TAG on branch $(CURRENT_BRANCH)..."; \
	git tag $$TAG && git push origin $$TAG; \
	echo "🚀 Creating GitHub prerelease..."; \
	gh release create $$TAG \
		--title "$$TAG" \
		--notes "Pre-release $$TAG" \
		--target $(CURRENT_BRANCH) \
		--prerelease \
		$(DIST_DIR)/*.tar.gz \
		$(DIST_DIR)/*.whl || true

release:
	@VERSION=$$(cat VERSION); \
	TAG=v$$VERSION; \
	echo "🏷️  Creating release tag $$TAG on branch $(CURRENT_BRANCH)..."; \
	git tag $$TAG && git push origin $$TAG; \
	echo "🚀 Creating GitHub release..."; \
	gh release create $$TAG \
		--title "$$TAG" \
		--notes "Release $$TAG" \
		--target $(CURRENT_BRANCH) \
		$(DIST_DIR)/*.tar.gz \
		$(DIST_DIR)/*.whl || true

# =====================
# Optional: help target
# =====================
help:
	@echo "📦 Available targets:"
	@$(foreach t,$(sort $(TARGETS)), echo "  $(t)";)
