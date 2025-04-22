# =====================
# Config
# =====================

# Actions per component
ACTIONS_miner := bump-major bump-minor bump-patch bump-alpha bump-rc
ACTIONS_validator := bump-major bump-minor bump-patch bump-alpha bump-rc

# Services per component
SERVICES_miner := neuron
SERVICES_validator := neuron redis

# All components
COMPONENTS := miner validator

# Get the current branch
CURRENT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

# Get the version script
BUMP_VERSION_SCRIPT = ./scripts/cicd/cicd_bump_version.py
UNBUMP_VERSION_SCRIPT = ./scripts/cicd/cicd_unbump_version.py

DIST_DIR = ./dist

# =============================
# Declare all targets as .PHONY
# =============================
TARGETS += clean build tag untag release prerelease unrelease unprerelease

# ======================
# Declare shared methods
# ======================
get_version_shell = $(shell \
  if [ -f $(1)/pyproject.toml ]; then \
    grep -E '^version\s*=\s*"([^"]+)"' $(1)/pyproject.toml | awk -F '"' '{print $$2}'; \
  elif [ -f $(1)/version.py ]; then \
    grep -oE '__version__ *= *["'"'"']([^"'"'"']+)["'"'"']' $(1)/version.py | sed -E 's/__version__ *= *["'"'"']([^"'"'"']+)["'"'"']/\1/'; \
  elif [ -f $(1)/VERSION ]; then \
    cat $(1)/VERSION | tr -d '\n'; \
  else \
    echo "VERSION_NOT_FOUND"; \
  fi)


define get_version
	if [ -f $(1)/version.py ]; then \
		grep -oE '__version__ *= *["'"'"']([^"'"'"']+)["'"'"']' $(1)/version.py | sed -E 's/__version__ *= *["'"'"']([^"'"'"']+)["'"'"']/\1/'; \
	elif [ -f $(1)/VERSION ]; then \
		cat $(1)/VERSION | tr -d '\n'; \
	elif [ -f $(1)/pyproject.toml ]; then \
		grep -E '^version\s*=\s*"([^"]+)"' $(1)/pyproject.toml | awk -F '"' '{print $$2}'; \
	else \
		echo "VERSION_NOT_FOUND"; \
	fi
endef

# ==================
# 🔨 Version Bumping
# ==================
# Root-level bump targets
TARGETS += bump-alpha bump-rc bump-patch bump-minor bump-major
TARGETS += unbump-alpha unbump-rc unbump-patch unbump-minor unbump-major

define bump_template
bump-$(1):
	@echo "🔧 bump-$(1) (skip=$(skip), only=$(only))"

	@only_root=false; \
	skip_root=false; \
	if [ -n "$(only)" ]; then \
		echo "$(only)" | grep -q -x "\." && only_root=true || only_root=false; \
	else \
		skip_root=false; \
		echo "$(skip)" | grep -q -x "\." && skip_root=true; \
	fi; \
	if [ "$$$$only_root" = true ] || { [ -z "$(only)" ] && [ "$$$$skip_root" = false ]; }; then \
		python3 $(BUMP_VERSION_SCRIPT) . $(1); \
		python3 $(BUMP_VERSION_SCRIPT) ./subvortex $(1); \
	fi

	@for comp in $$(COMPONENTS); do \
		if [ -n "$$(only)" ]; then \
			echo "$$(only)" | grep -q -x "$$$$comp" || continue; \
		elif echo "$$(skip)" | grep -q -x "$$$$comp"; then \
			continue; \
		fi; \
		python3 $(BUMP_VERSION_SCRIPT) subvortex/$$$$comp $(1); \
	done

	@for comp in $$(COMPONENTS); do \
		case "$$$$comp" in \
			miner) SERVICES="$(SERVICES_miner)";; \
			validator) SERVICES="$(SERVICES_validator)";; \
			*) echo "Unknown component: $$$$comp"; exit 1;; \
		esac; \
		for svc in $$$$SERVICES; do \
			entry="$$$$comp/$$$$svc"; \
			if [ -n "$$(only)" ]; then \
				echo "$$(only)" | grep -q -x "$$$$entry" || continue; \
			elif echo "$$(skip)" | grep -q -x "$$$$entry"; then \
				continue; \
			fi; \
			python3 $(BUMP_VERSION_SCRIPT) subvortex/$$$$entry $(1); \
		done \
	done
endef

define unbump_template
unbump-$(1):
	@echo "🔄 unbump-$(1) (skip=$(skip), only=$(only))"

	@only_root=false; \
	skip_root=false; \
	if [ -n "$(only)" ]; then \
		echo "$(only)" | grep -q -x "\." && only_root=true || only_root=false; \
	else \
		skip_root=false; \
		echo "$(skip)" | grep -q -x "\." && skip_root=true; \
	fi; \
	if [ "$$$$only_root" = true ] || { [ -z "$(only)" ] && [ "$$$$skip_root" = false ]; }; then \
		python3 $(UNBUMP_VERSION_SCRIPT) . $(1); \
		python3 $(UNBUMP_VERSION_SCRIPT) ./subvortex $(1); \
	fi

	@for comp in $$(COMPONENTS); do \
		if [ -n "$$(only)" ]; then \
			echo "$$(only)" | grep -q -x "$$$$comp" || continue; \
		elif echo "$$(skip)" | grep -q -x "$$$$comp"; then \
			continue; \
		fi; \
		python3 $(UNBUMP_VERSION_SCRIPT) subvortex/$$$$comp $(1); \
	done

	@for comp in $$(COMPONENTS); do \
		case "$$$$comp" in \
			miner) SERVICES="$(SERVICES_miner)";; \
			validator) SERVICES="$(SERVICES_validator)";; \
			*) echo "Unknown component: $$$$comp"; exit 1;; \
		esac; \
		for svc in $$$$SERVICES; do \
			entry="$$$$comp/$$$$svc"; \
			if [ -n "$$(only)" ]; then \
				echo "$$(only)" | grep -q -x "$$$$entry" || continue; \
			elif echo "$$(skip)" | grep -q -x "$$$$entry"; then \
				continue; \
			fi; \
			python3 $(UNBUMP_VERSION_SCRIPT) subvortex/$$$$entry $(1); \
		don
endef

$(foreach level, patch minor major alpha rc,\
	$(eval $(call bump_template,$(level)))\
	$(eval $(call unbump_template,$(level)))\
)

# Per-component bump shortcuts
$(foreach comp,$(COMPONENTS),\
  $(foreach action,patch minor major alpha rc,\
  	$(eval TARGETS += bump-$(comp)-$(action) unbump-$(comp)-$(action))\
  	$(eval bump-$(comp)-$(action): ; \
  		python3 $(BUMP_VERSION_SCRIPT) subvortex/$(comp) $(action) \
  	) \
	$(eval unbump-$(comp)-$(action): ; \
  		python3 $(BUMP_VERSION_SCRIPT) subvortex/$(comp) $(action) \
  	) \
	$(foreach svc,$(SERVICES_$(comp)),\
		$(eval TARGETS += bump-$(comp)-$(svc)-$(action) unbump-$(comp)-$(svc)-$(action))\
		$(eval bump-$(comp)-$(svc)-$(action): ; \
			python3 $(BUMP_VERSION_SCRIPT) subvortex/$(comp)/$(svc) $(action) \
		) \
		$(eval unbump-$(comp)-$(svc)-$(action): ; \
			python3 $(BUMP_VERSION_SCRIPT) subvortex/$(comp)/$(svc) $(action) \
		) \
	)\
  ) \
)

# ========
# 🧪 Build
# ========
define clean_github_component
	@echo "🧹 Cleaning GitHub build for $(1)..."
	@rm -rf $(DIST_DIR)/subvortex_$(1)* build *.egg-info
	@rm -f pyproject.toml
	@echo "✅ GitHub clean complete for $(1)"
endef

define build_github_component
	@$(MAKE) clean-$(1)
	@echo "📦 Building GitHub asset for $(1) with pyproject-$(1).toml..."
	@cp pyproject-$(1).toml pyproject.toml
	@python3 -m build --sdist --wheel -o dist
	@rm pyproject.toml
	@for f in dist/subvortex-*; do \
		[ -f "$$f" ] || continue; \
		newf=$${f/subvortex-/subvortex_$(1)-}; \
		echo "➡️  Renaming: $$f -> $$newf"; \
		mv "$$f" "$$newf"; \
	done
	@echo "✅ GitHub asset build done for $(1)"
endef

# Build and clean targets per component and category
$(foreach comp,$(COMPONENTS), \
	$(eval TARGETS += build-$(comp) clean-${comp}) \
	$(eval build-$(comp): ; $$(call build_github_component,$(comp))) \
	$(eval clean-$(comp): ; $$(call clean_github_component,$(comp))) \
)

# Global
build: $(foreach comp,$(COMPONENTS),build-$(comp))
clean: $(foreach comp,$(COMPONENTS),clean-$(comp))

# ============
# 🏷️ Tag/Untag
# ============
define create_github_tag
	@VERSION=$(call get_version_shell, .); \
	echo "🏷️ Creating GitHub tag v$$VERSION"; \
	git tag -a "v$$VERSION" -m "Release version $$VERSION"; \
	git push origin "v$$VERSION";
endef

define delete_github_tag
	@VERSION=$(call get_version_shell, .); \
	echo "🗑️ Deleting GitHub tag v$$VERSION"; \
	git tag -d "v$$VERSION"; \
	git push origin ":refs/tags/v$$VERSION";
endef

# Github
$(foreach comp,$(COMPONENTS), \
	$(eval TARGETS += tag-$(comp) untag-${comp}) \
	$(eval tag-$(comp): ; $$(call create_github_tag,$(comp))) \
	$(eval untag-$(comp): ; $$(call delete_github_tag,$(comp))) \
)

# Global
tag: tag-auto_upgrader
untag: untag-auto_upgrader


# ====================
# 🚀 Release/UnRelease
# ====================
define github_release
	@VERSION=$$(cat VERSION); \
 	TAG=v$$VERSION; \
 	echo "🚀 Creating GitHub release..."; \
 	gh release create $$TAG \
 		--title "$$TAG" \
 		--notes "Release $$TAG" \
 		--target $(CURRENT_BRANCH) \
 		$(DIST_DIR)/*.tar.gz \
 		$(DIST_DIR)/*.whl || true
endef

define github_unrelease
	@COMP=$(1); \
	VERSION=$$(call get_version,subvortex/$$$$COMP); \
	echo "🗑️ Deleting GitHub release v$$VERSION for $$$$COMP"; \
	gh release delete "v$$VERSION" --yes || true;
endef

define github_prerelease
 	@VERSION=$$(cat VERSION); \
 	TAG=v$$VERSION; \
 	echo "🚀 Creating GitHub prerelease..."; \
 	gh release create $$TAG \
 		--title "$$TAG" \
 		--notes "Pre-release $$TAG" \
 		--target $(CURRENT_BRANCH) \
 		--prerelease \
 		$(DIST_DIR)/*.tar.gz \
 		$(DIST_DIR)/*.whl || true
endef

define github_unprerelease
 	@VERSION=$$(cat VERSION); \
 	TAG=v$$VERSION; \
	echo "🗑️ Deleting GitHub prerelease v$$VERSION"; \
	gh release delete $$TAG --yes || true;
endef

# Auto-generate rules per component
$(foreach comp,$(COMPONENTS), \
  $(eval TARGETS += release-$(comp) prerelease-$(comp) unrelease-$(comp) unprerelease-$(comp)) \
  $(eval release-github-$(comp): ; $$(call github_release,$(comp))) \
  $(eval prerelease-github-$(comp): ; $$(call github_prerelease,$(comp))) \
  $(eval unrelease-github-$(comp): ; $$(call github_unrelease,$(comp))) \
  $(eval unprerelease-github-$(comp): ; $$(call github_unprerelease,$(comp))) \
)

# Githug
release-github: $(foreach comp,$(COMPONENTS),release-github-$(comp))
prerelease-github: $(foreach comp,$(COMPONENTS),prerelease-github-$(comp))
unrelease-github: $(foreach comp,$(COMPONENTS),unrelease-github-$(comp))
unprerelease-github: $(foreach comp,$(COMPONENTS),unprerelease-github-$(comp))

# Global
release: release-github
unrelease: unrelease-github

# =====================
# Add the last target
# =====================
.PHONY: $(TARGETS) help

# =====================
# Optional: help target
# =====================
help:
	@echo "📦 CI/CD Targets:"
	@echo ""
	@echo "🔧 Version Bump Commands"
	@echo ""
	@echo "  bump-patch                    – Patch all components"
	@echo "  bump-minor                    – Minor bump for all components"
	@echo "  bump-major                    – Major bump for all components"
	@echo "  bump-alpha                    – Alpha pre-release bump for all"
	@echo "  bump-rc                       – RC pre-release bump for all"
	@echo "  bump-version                  – New pre-release for all"
	@echo ""
	@echo "🔧 Role-level Bumps"
	@echo "  bump-[role]-patch             – Patch [role] and its services"
	@echo "  bump-[role]-minor             – Minor bump for [role] and its services"
	@echo "  bump-[role]-major             – Major bump for [role] and its services"
	@echo "  bump-[role]-alpha             – Alpha bump for [role] and its services"
	@echo "  bump-[role]-rc                – RC bump for [role] and its services"
	@echo ""
	@echo "🔧 Service-level Bumps"
	@echo "  bump-[role]-[service]-patch   – Patch [role]/[service]"
	@echo "  bump-[role]-[service]-minor   – Minor bump for [role]/[service]"
	@echo "  bump-[role]-[service]-major   – Major bump for [role]/[service]"
	@echo "  bump-[role]-[service]-alpha   – Alpha bump for [role]/[service]"
	@echo "  bump-[role]-[service]-rc      – RC bump for [role]/[service]"
	@echo ""
	@echo "🧪 Build/Clean:"
	@echo "  build                         – Build all components"
	@echo "  clean                         – Clean all components"
	@echo ""
	@echo "  build-[role]                  – Build [role]"
	@echo "  clean-[role]                  – Clean [role]"
	@echo ""
	@echo "  build-[executor]              – Build all components using [executor]"
	@echo "  clean-[executor]              – Clean all components using [executor]"
	@echo ""
	@echo "  build-[executor]-[role]       – Build [role] using [executor]"
	@echo "  clean-[executor]-[role]       – Clean [role] using [executor]"
	@echo ""
	@echo "🏷️ Tag/Untag:"
	@echo "  tag                           – Tag all (Docker + GitHub)"
	@echo "  untag                         – Untag all (Docker + GitHub)"
	@echo ""
	@echo "  tag-[executor]                – Tag all with [executor] (Docker + Github)"
	@echo "  untag-[executor]              – Untag all with [executor] (Docker + Github)"
	@echo ""
	@echo "  tag-[executor]-[role]         – Tag [role] with [executor] (Docker)"
	@echo "  untag-[executor]-[role]       – Untag [role] with [executor] (Docker)"
	@echo ""
	@echo "🚀 Release/Unrelease:"
	@echo "  release                       – Release all (GitHub + Docker)"
	@echo "  unrelease                     – Unrelease all (GitHub + Docker)"
	@echo "  release-github                – Create GitHub releases"
	@echo "  unrelease-github              – Remove GitHub releases"
	@echo "  release-docker                – Push Docker image tags to the registry"
	@echo "  unrelease-docker              – Remove Docker image tags from the registry"
	@echo "  release-github-miner          – Release GitHub for miner"
	@echo "  unrelease-github-miner        – Remove release GitHub for miner"
	@echo "  release-docker-miner		   – Push Docker miner image tag to the registry"
	@echo "  unrelease-docker-miner        – Remove Docker miner image tag from the registry"
	@echo "  release-github-validator      – Release GitHub for validator"
	@echo "  unrelease-github-validator    – Remove release GitHub for validator"
	@echo "  release-docker-validator      – Push Docker validator image tag to the registry"
	@echo "  unrelease-docker-validator    – Remove Docker validator image tag from the registry"

targets:
	@echo "📋 Available Dynamic Targets:"
	@echo ""
	@printf "  %s\n" $(sort $(TARGETS))