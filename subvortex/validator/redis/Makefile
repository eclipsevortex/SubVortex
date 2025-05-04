.PHONY: patch minor major alpha rc prerelease upload clean release

GIT_TAG_PREFIX = v
CURRENT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
VERSION_SCRIPT = ../../../scripts/cicd/cicd_bump_version.py
DIST_DIR = ../../dist
STAGING_DIR = build
PROJECT_NAME = subvortex_valildator
BASE_PYPROJECT = pyproject.toml

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

delete-tag:
ifndef TAG
	$(error ❌ Please specify the tag to delete: make delete-tag TAG=vX.Y.Z)
endif
	@echo "🔧 Deleting local tag $(TAG)..."
	@git tag -d $(TAG) || echo "⚠️  Local tag $(TAG) does not exist"
	@echo "🌐 Deleting remote tag $(TAG)..."
	@git push origin :refs/tags/$(TAG) || echo "⚠️  Remote tag $(TAG) may not exist"

tag: 
	@VERSION=$$(grep -m 1 '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	TAG=$(GIT_TAG_PREFIX)$$VERSION; \
	echo "🏷️  Creating prerelease tag $$TAG on branch $(CURRENT_BRANCH)..."; \
	git tag $$TAG && git push origin $$TAG;
	
.PHONY: github-release github-prerelease
github-prerelease:
	@VERSION=$$(grep -m 1 '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	TAG=$(GIT_TAG_PREFIX)$$VERSION; \
	echo "🏷️  Creating prerelease tag $$TAG on branch $(CURRENT_BRANCH)..."; \
	git tag $$TAG && git push origin $$TAG; \
	echo "🚀 Creating GitHub prerelease..."; \
	gh release create $$TAG \
		--title "$$TAG" \
		--notes "Pre-release $$TAG" \
		--target $(CURRENT_BRANCH) \
		--prerelease \
		$(DIST_DIR)/$(PROJECT_NAME)/*.tar.gz \
		$(DIST_DIR)/$(PROJECT_NAME)/*.whl || true

github-release:
	@VERSION=$$(grep -m 1 '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	TAG=$(GIT_TAG_PREFIX)$$VERSION; \
	echo "🏷️  Creating release tag $$TAG on branch $(CURRENT_BRANCH)..."; \
	git tag $$TAG && git push origin $$TAG; \
	echo "🚀 Creating GitHub release..."; \
	gh release create $$TAG \
		--title "$$TAG" \
		--notes "Release $$TAG" \
		--target $(CURRENT_BRANCH) \
		$(DIST_DIR)/$(PROJECT_NAME)/*.tar.gz \
		$(DIST_DIR)/$(PROJECT_NAME)/*.whl || true

clean:
	rm -rf $(DIST_DIR) *.egg-info **/*.egg-info build/

release: patch build upload github-release

prerelease: patch build upload github-prerelease
