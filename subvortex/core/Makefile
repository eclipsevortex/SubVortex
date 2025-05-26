# =========
# 🧪 Tests
# =========
TARGETS += test

test:
	PYTHONPATH=../.. pytest . $(ARGS)

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
	@echo "  test                          – Run pytest in all service folders"

targets:
	@echo "📋 Available Dynamic Targets:"
	@echo ""
	@printf "  %s\n" $(sort $(TARGETS))