# =====================
# Config
# =====================

# Export environment variables to all targets
include .env
DOCKER_PASSWORD := $(SUBVORTEX_DOCKER_TOKEN)
export DOCKER_PASSWORD

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
TARGETS += tag untag
tag: 
	@VERSION=$(call get_version_shell, .); \
	echo "🏷️ Creating GitHub tag v$$VERSION"; \
	git tag -a "v$$VERSION" -m "Release version $$VERSION"; \
	git push origin "v$$VERSION";

untag: 
	@VERSION=$(call get_version_shell, .); \
	echo "🗑️ Deleting GitHub tag v$$VERSION"; \
	git tag -d "v$$VERSION"; \
	git push origin ":refs/tags/v$$VERSION";

# ====================
# 🚀 Release/UnRelease
# ====================
TARGETS += release unrelease prerelease unprerelease
unprerelease:
	@VERSION=$$(cat VERSION); \
 	TAG=v$$VERSION; \
	\
	(gh release view "$$TAG" &>/dev/null && \
	  echo "🗑️  Deleting GitHub prerelease $$TAG..." && \
	  gh release delete "$$TAG" --yes || \
	  echo "⚠️ Failed to delete or prerelease not found — continuing..."); \
	\
	for comp in subvortex/*; do \
		[ -d "$$comp" ] || continue; \
		comp_name=$$(basename "$$comp"); \
		case $$comp_name in \
			miner) services="neuron" ;; \
			validator) services="neuron redis" ;; \
			*) services="$$comp_name" ;; \
		esac; \
		for service in $$services; do \
			service_path="$$comp/$$service"; \
			if [ -f "$$service_path/pyproject.toml" ] || [ -f "$$service_path/version.py" ]; then \
				.github/scripts/on_release_deleted.sh"$$comp_name" "$$service" "$$TAG"; \
			fi; \
		done; \
	done

prerelease:
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

unrelease:
	@VERSION=$$(cat VERSION); \
 	TAG=v$$VERSION; \
	\
	(gh release view "$$TAG" &>/dev/null && \
	  echo "🗑️  Deleting GitHub release $$TAG..." && \
	  gh release delete "$$TAG" --yes || \
	  echo "⚠️ Failed to delete or release not found — continuing..."); \
	\
	for comp in subvortex/*; do \
		[ -d "$$comp" ] || continue; \
		comp_name=$$(basename "$$comp"); \
		case $$comp_name in \
			miner) services="neuron" ;; \
			validator) services="neuron redis" ;; \
			*) services="$$comp_name" ;; \
		esac; \
		for service in $$services; do \
			service_path="$$comp/$$service"; \
			if [ -f "$$service_path/pyproject.toml" ] || [ -f "$$service_path/version.py" ]; then \
				.github/scripts/on_release_deleted.sh"$$comp_name" "$$service" "$$TAG"; \
			fi; \
		done; \
	done
release:
	@VERSION=$$(cat VERSION); \
 	TAG=v$$VERSION; \
 	echo "🚀 Creating GitHub release..."; \
 	gh release create $$TAG \
 		--title "$$TAG" \
 		--notes "Release $$TAG" \
 		--target $(CURRENT_BRANCH) \
 		$(DIST_DIR)/*.tar.gz \
 		$(DIST_DIR)/*.whl || true

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
	@echo "🏷️ Tag/Untag:"
	@echo "  tag                           – Tag all components"
	@echo "  untag                         – Untag all components"
	@echo ""
	@echo "🚀 Release/Unrelease:"
	@echo "  release                       – Release all components"
	@echo "  unrelease                     – Unrelease all components"
	@echo "  prerelease                    – Release all components"
	@echo "  unprerelease                  – Unrelease all components"

targets:
	@echo "📋 Available Dynamic Targets:"
	@echo ""
	@printf "  %s\n" $(sort $(TARGETS))