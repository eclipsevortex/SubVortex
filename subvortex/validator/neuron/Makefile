.PHONY: bump-patch bump-minor bump-major bump-alpha bump-rc clean

VERSION_SCRIPT = ../../../scripts/cicd/cicd_bump_version.py
DIST_DIR = ../../dist

bump-patch:
	@python3 $(VERSION_SCRIPT) patch

bump-minor:
	@python3 $(VERSION_SCRIPT) minor

bump-ajor:
	@python3 $(VERSION_SCRIPT) major

bump-alpha:
	@python3 $(VERSION_SCRIPT) alpha

bump-rc:
	@python3 $(VERSION_SCRIPT) rc

clean:
	rm -rf $(DIST_DIR) *.egg-info **/*.egg-info build/