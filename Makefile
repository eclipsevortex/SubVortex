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
VERSION_SCRIPT = ./scripts/cicd/cicd_bump_version.py

DIST_DIR = ./dist

# =============================
# Declare all targets as .PHONY
# =============================
TARGETS += clean clean-miner clean-validator \
	clean-github clean-github-miner clean-github-validator \
	clean-docker clean-docker-miner clean-docker-validator \
	build build-miner build-validator \
	build-github build-github-miner build-github-validator \
	build-docker build-docker-miner build-docker-validator \
	tag tag-miner tag-validator \
	tag-github tag-github-miner tag-github-validator \
	tag-docker tag-docker-miner tag-docker-validator \
	untag untag-miner untag-validator \
	untag-github untag-github-miner untag-github-validator \
	untag-docker untag-docker-miner untag-docker-validator \
	release release-miner release-validator \
	prerelease release-miner prerelease-validator \
	release-github release-github-miner release-github-validator \
	prerelease-github prerelease-github-miner prerelease-github-validator \
	release-docker release-docker-miner release-docker-validator \
	prerelease-docker prerelease-docker-miner prerelease-docker-validator \


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
		python3 $(VERSION_SCRIPT) . $(1); \
	fi

	@for comp in $$(COMPONENTS); do \
		if [ -n "$$(only)" ]; then \
			echo "$$(only)" | grep -q -x "$$$$comp" || continue; \
		elif echo "$$(skip)" | grep -q -x "$$$$comp"; then \
			continue; \
		fi; \
		python3 $(VERSION_SCRIPT) subvortex/$$$$comp $(1); \
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
			python3 $(VERSION_SCRIPT) subvortex/$$$$entry $(1); \
		done \
	done
endef

$(foreach level,patch minor major alpha rc,$(eval $(call bump_template,$(level))))

# Per-component bump shortcuts
$(foreach comp,$(COMPONENTS),\
  $(foreach action,patch minor major alpha rc,\
  	$(eval TARGETS += bump-$(comp)-$(action))\
  	$(eval bump-$(comp)-$(action): ; \
  		python3 $(VERSION_SCRIPT) subvortex/$(comp) $(action) && \
  		$(foreach svc,$(SERVICES_$(comp)),python3 $(VERSION_SCRIPT) subvortex/$(comp)/$(svc) $(action);) \
  	) \
  ) \
)

# Per-service bump shortcuts
$(foreach comp,$(COMPONENTS),\
  $(foreach svc,$(SERVICES_$(comp)),\
    $(foreach action,patch minor major alpha rc,\
      $(eval TARGETS += bump-$(comp)-$(svc)-$(action))\
      $(eval bump-$(comp)-$(svc)-$(action): ; \
        python3 $(VERSION_SCRIPT) subvortex/$(comp)/$(svc) $(action) \
      )\
    )\
  )\
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

define clean_docker_component
	@COMP=$(1); \
	SERVICES="$$(SERVICES_$(1))"; \
	VERSION=$$$$($$(call get_version, subvortex/$$$$COMP)); \
	for service in $$$$SERVICES; do \
		IMAGE_NAME=subvortex/subvortex-$$$$COMP-$$$$service:$$$$VERSION; \
		echo "🧹 Removing Docker image $$$$IMAGE_NAME..."; \
		docker rmi $$$$IMAGE_NAME || true; \
	done
	@echo "✅ Docker clean complete for $(1)"
endef

define build_github_component
	@$(MAKE) clean-github-$(1)
	@echo "📦 Building GitHub asset for $(1) with pyproject-$(1).toml..."
	@cp pyproject-$(1).toml pyproject.toml
	@python3 -m build --sdist --wheel -o dist
	@rm pyproject.toml
	@for f in dist/subvortex-*; do \
		[ -f "$$$$f" ] || continue; \
		newf=$$$${f/subvortex-/subvortex_$(1)-}; \
		echo "➡️  Renaming: $$$$f -> $$$$newf"; \
		mv "$$$$f" "$$$$newf"; \
	done
	@echo "✅ GitHub asset build done for $(1)"
endef
# VERSION=`grep -oE "__version__ *= *[\"\\'\']([^\"\\'\']+)[\"\\'\']" subvortex/$$$$COMP/version.py | sed -E "s/__version__ *= *[\"\\'\']([^\"\\'\']+)[\"\\'\']/\\1/"`; \

# define build_docker_component
# 	@COMP=$(1); \
# 	SERVICES="$$(SERVICES_$(1))"; \
# 	docker buildx inspect multiarch-builder >/dev/null 2>&1 || docker buildx create --name multiarch-builder --use; \
# 	docker buildx use multiarch-builder; \
# 	docker run --rm --privileged multiarch/qemu-user-static --reset -p yes; \
# 	for service in $$$$SERVICES; do \
# 		path=subvortex/$$$$COMP; \
# 		MINER_VERSION=$$$$($$(call get_version, $$$$path)); \
# 		path=subvortex/$$$$COMP/$$$$service; \
# 		VERSION=$$$$($$(call get_version, $$$$path)); \
# 		IMAGE_NAME=subvortex/subvortex-$$$$COMP-$$$$service:$$$$VERSION; \
# 		DOCKERFILE=subvortex/$$$$COMP/$$$$service/Dockerfile; \
# 		echo "🐳 Building $$$$IMAGE_NAME from $$$$DOCKERFILE..."; \
# 		docker buildx build --load --platform linux/amd64,linux/arm64 --build-arg VERSION=$$$$VERSION --build-arg MINER_VERSION=$$$$MINER_VERSION -t $$$$IMAGE_NAME -f $$$$DOCKERFILE . || exit 1; \
# 		echo "✅ Built $$$$IMAGE_NAME"; \
# 	done
# endef

define build_docker_component
	@COMP=$(1); \
	SERVICES="$$(SERVICES_$(1))"; \
	echo "🔧 Running setup-buildx..."; \
	docker buildx use default; \
	docker buildx inspect --bootstrap; \
	for service in $$$$SERVICES; do \
		path=subvortex/$$$$COMP; \
		MINER_VERSION=$$$$($$(call get_version, $$$$path)); \
		path=subvortex/$$$$COMP/$$$$service; \
		VERSION=$$$$($$(call get_version, $$$$path)); \
		IMAGE_NAME=subvortex/subvortex-$$$$COMP-$$$$service:$$$$VERSION; \
		DOCKERFILE=subvortex/$$$$COMP/$$$$service/Dockerfile; \
		for ARCH in amd64 arm64; do \
			TAG=$$$$IMAGE_NAME-$$$$ARCH; \
			echo "🐳 Building $$$$TAG from $$$$DOCKERFILE..."; \
			docker buildx build --platform=linux/$$ARCH --load --build-arg VERSION=$$$$VERSION --build-arg MINER_VERSION=$$$$MINER_VERSION -t $$$$TAG -f $$$$DOCKERFILE . || exit 1; \
			echo "✅ Built $$$$TAG"; \
		done \
	done
endef


define build_docker_component
	@COMP=$(1); \
	SERVICES="$$(SERVICES_$(1))"; \
	for service in $$$$SERVICES; do \
		path=subvortex/$$$$COMP; \
		MINER_VERSION=$$$$($$(call get_version, $$$$path)); \
		path=subvortex/$$$$COMP/$$$$service; \
		VERSION=$$$$($$(call get_version, $$$$path)); \
		IMAGE_NAME=subvortex/subvortex-$$$$COMP-$$$$service:$$$$VERSION; \
		DOCKERFILE=subvortex/$$$$COMP/$$$$service/Dockerfile; \
		echo "🐳 Building $$$$IMAGE_NAME from $$$$DOCKERFILE..."; \
		docker buildx build --platform linux/amd64,linux/arm64 --build-arg VERSION=$$$$VERSION --build-arg MINER_VERSION=$$$$MINER_VERSION -t $$$$IMAGE_NAME -f $$$$DOCKERFILE --push . || exit 1; \
		echo "✅ Built $$$$IMAGE_NAME"; \
	done
endef

# Build and clean targets per component and category
$(foreach comp,$(COMPONENTS), \
	$(eval build-github-$(comp): ; $(call build_github_component,$(comp))) \
	$(eval build-docker-$(comp): ; $(call build_docker_component,$(comp))) \
	$(eval clean-github-$(comp): ; $(call clean_github_component,$(comp))) \
	$(eval clean-docker-$(comp): ; $(call clean_docker_component,$(comp))) \
)

build-github: $(foreach comp,$(COMPONENTS),build-github-$(comp))
build-docker: $(foreach comp,$(COMPONENTS),build-docker-$(comp))
build: build-github build-docker

clean-github: $(foreach comp,$(COMPONENTS),clean-github-$(comp))
clean-docker: $(foreach comp,$(COMPONENTS),clean-docker-$(comp))
clean: clean-github clean-docker

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

define create_docker_tag
	@COMP=miner; \
	SERVICES="$(SERVICES_miner)"; \
	for service in $$$$SERVICES; do \
		path=subvortex/$$$$COMP/$$$$service; \
		VERSION=$$$$($$(call get_version, $$$$path)); \
		IMAGE_NAME=subvortex/subvortex-$$$$COMP-$$$$service:$$$$VERSION; \
		for ARCH in amd64 arm64; do \
			TAG=$$IMAGE_NAME-$$ARCH; \
			echo "📤 Releasing Docker image: $$$$TAG"; \
			docker push $$$$TAG || exit 1; \
	done
endef

define delete_docker_tag
	@COMP=miner; \
	SERVICES="$(SERVICES_miner)"; \
	. .env; \
	for service in $$$$SERVICES; do \
		path=subvortex/$$$$COMP/$$$$service; \
		VERSION=$$$$($$(call get_version, $$$$path)); \
		echo "🗑️ Deleting tag $$$$VERSION from Docker Hub"; \
		curl -s -X DELETE -H "Authorization: JWT $$$$SUBVORTEX_DOCKER_TOKEN" \
			https://hub.docker.com/v2/repositories/subvortex/subvortex-$$$$COMP-$$$$service/tags/$$$$VERSION/ || true; \
	done;
endef


$(foreach comp,$(COMPONENTS), \
	$(eval tag-docker-$(comp): ; $(call create_docker_tag,$(comp))) \
	$(eval untag-docker-$(comp): ; $(call delete_docker_tag,$(comp))) \
)

tag-github: 
	$(create_github_tag)

untag-github: 
	$(delete_github_tag)

tag-docker: $(foreach comp,$(COMPONENTS),tag-docker-$(comp))
untag-docker: $(foreach comp,$(COMPONENTS),untag-docker-$(comp))

tag: tag-github tag-docker
untag: untag-github untag-docker


# ====================
# 🚀 Release/UnRelease
# ====================
define docker_release
	@COMP=$(1); \
	SERVICES="$(SERVICES_$(1))"; \
	for service in $$$$SERVICES; do \
		path=subvortex/$$$$COMP/$$$$service; \
		VERSION=$$$$($$(call get_version, $$$$path)); \
		IMAGE_NAME=subvortex/subvortex-$$$$COMP-$$$$service:$$$$VERSION; \
		echo "🔁 Tagging as latest"; \
		docker tag $$$$IMAGE_NAME subvortex/subvortex-$$$$COMP-$$$$service:latest; \
		docker push subvortex/subvortex-$$$$COMP-$$$$service:latest; \
	done;
endef

define docker_unrelease
	@COMP=$(1); \
	SERVICES="$$(SERVICES_$(1))"; \
	. .env; \
	for service in $$$$SERVICES; do \
		path=subvortex/$$$$COMP/$$$$service; \
		VERSION=$$$$($$(call get_version, $$$$path)); \
		echo "🗑️ Deleting floating tag 'latest' from Docker Hub for subvortex/subvortex-$$$$COMP-$$$$service"; \
		curl -s -X DELETE -H "Authorization: JWT $$$$SUBVORTEX_DOCKER_TOKEN" \
			https://hub.docker.com/v2/repositories/subvortex/subvortex-$$$$COMP-$$$$service/tags/latest/ || true; \
	done;
endef

define docker_prerelease
	@COMP=$(1); \
	SERVICES="$(SERVICES_$(1))"; \
	for service in $$$$SERVICES; do \
		path=subvortex/$$$$COMP/$$$$service; \
		VERSION=$$$$($$(call get_version, $$$$path)); \
		IMAGE_NAME=subvortex/subvortex-$$$$COMP-$$$$service:$$$$VERSION; \
		TAGS="dev"; \
		if echo "$$$$VERSION" | grep -q "rc"; then \
			TAGS="dev stable"; \
		fi; \
		for tag in $$$$TAGS; do \
			echo "🔁 Tagging as floating tag: $$$$tag"; \
			docker tag $$$$IMAGE_NAME subvortex/subvortex-$$$$COMP-$$$$service:$$$$tag; \
			docker push subvortex/subvortex-$$$$COMP-$$$$service:$$$$tag; \
		done; \
	done;
endef

define docker_unprerelease
	@COMP=$(1); \
	SERVICES="$$(SERVICES_$(1))"; \
	. .env; \
	for service in $$$$SERVICES; do \
		path=subvortex/$$$$COMP/$$$$service; \
		VERSION=$$$$($$(call get_version, $$$$path)); \
		TAGS="dev"; \
		if echo "$$$$VERSION" | grep -q "rc"; then \
			TAGS="dev stable"; \
		fi; \
		for tag in $$$$TAGS; do \
			echo "🗑️ Deleting floating tag '$$$$tag' from Docker Hub for subvortex/subvortex-$$$$COMP-$$$$service"; \
			curl -s -X DELETE -H "Authorization: JWT $$$$SUBVORTEX_DOCKER_TOKEN" \
				https://hub.docker.com/v2/repositories/subvortex/subvortex-$$$$COMP-$$$$service/tags/$$$$tag/ || true; \
		done; \
	done;
endef

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
## Docker releases per component
$(foreach comp,$(COMPONENTS), \
	$(eval TARGETS += prerelease-docker-$(comp))\
	$(eval prerelease-docker-$(comp): ; $(call docker_prerelease,$(comp))) \
)
$(foreach comp,$(COMPONENTS), \
	$(eval TARGETS += release-docker-$(comp))\
	$(eval release-docker-$(comp): ; $(call docker_release,$(comp))) \
)

## Docker unreleases per component
$(foreach comp,$(COMPONENTS), \
	$(eval TARGETS += unprerelease-docker-$(comp))\
	$(eval unprerelease-docker-$(comp): ; $(call docker_unprerelease,$(comp))) \
)
$(foreach comp,$(COMPONENTS), \
	$(eval TARGETS += unrelease-docker-$(comp))\
	$(eval unrelease-docker-$(comp): ; $(call docker_unrelease,$(comp))) \
)

## GitHub releases per component
$(foreach comp,$(COMPONENTS), \
	$(eval release-github-$(comp): ; $(call github_release,$(comp))) \
)

## GitHub unreleases per component
$(foreach comp,$(COMPONENTS), \
	$(eval unrelease-github-$(comp): ; $(call github_unrelease,$(comp))) \
)

# Github release/unrelease
release-github:
	$(github_release)

prerelease-github:
	$(github_prerelease)

unrelease-github:
	$(github_unrelease)

unprerelease-github:
	$(github_unprerelease)

# Docker release/unrelease
release-docker: $(foreach comp,$(COMPONENTS),release-docker-$(comp))
prerelease-docker: $(foreach comp,$(COMPONENTS),prerelease-docker-$(comp))
unrelease-docker: $(foreach comp,$(COMPONENTS),unrelease-docker-$(comp))
unprerelease-docker: $(foreach comp,$(COMPONENTS),unprerelease-docker-$(comp))

# Global release/unrelease
release: release-github release-docker
prerelease: prerelease-github prerelease-docker

unrelease: unrelease-github unrelease-docker
unprerelease: unprerelease-github unprerelease-docker


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