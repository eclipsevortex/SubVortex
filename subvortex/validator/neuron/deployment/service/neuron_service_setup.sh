#!/bin/bash

set -euo pipefail

# Ensure script run as root
if [[ "$EUID" -ne 0 ]]; then
    echo "🛑 This script must be run as root. Re-running with sudo..."
    exec sudo "$0" "$@"
fi

# Determine working directory: prefer SUBVORTEX_WORKING_DIR, fallback to script location
SCRIPT_DIR="$(cd "$(dirname "$(python3 -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$0")")" && pwd)"

# Find project root by walking up until LICENSE is found
find_project_root() {
    local dir="$1"
    while [[ "$dir" != "/" ]]; do
        [[ -f "$dir/LICENSE" ]] && { echo "$dir"; return; }
        dir="$(dirname "$dir")"
    done
    return 1
}

PROJECT_ROOT="$(find_project_root "$SCRIPT_DIR")" || {
    echo "❌ Could not detect project root (LICENSE not found)"
    exit 1
}

# Resolve final working directory
if [[ -n "${SUBVORTEX_WORKING_DIR:-}" ]]; then
    REL_PATH="${SCRIPT_DIR#$PROJECT_ROOT/}"
    TARGET_DIR="$SUBVORTEX_WORKING_DIR/$REL_PATH"
    [[ -d "$TARGET_DIR" ]] || { echo "❌ Target directory does not exist: $TARGET_DIR"; exit 1; }
    echo "📁 Using SUBVORTEX_WORKING_DIR: $TARGET_DIR"
    cd "$TARGET_DIR/../.."
else
    echo "📁 Using fallback PROJECT_ROOT: $SCRIPT_DIR"
    cd "$SCRIPT_DIR/../.."
fi

echo "📍 Working directory: $(pwd)"

echo "🐍 Setting up Python virtual environment..."

# Create virtual environment
echo "🔧 Creating venv..."
python3 -m venv venv

# Activate virtual environment
echo "🚀 Activating venv..."
source venv/bin/activate

# Install dependencies
if [[ -f "requirements.txt" ]]; then
    echo "📦 Installing Python dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found — skipping dependency installation."
fi

# Ensure pyproject.toml is present (local execution only)
if [[ ! -f "../../../pyproject.toml" ]]; then
    if [[ -f "../../../pyproject-miner.toml" ]]; then
        echo "📄 pyproject.toml not found, copying pyproject-validator.toml..."
        cp ../../../pyproject-validator.toml ../../../pyproject.toml
    else
        echo "❌ pyproject.toml and pyproject-validator.toml both not found. Cannot proceed."
        exit 1
    fi
fi

# Install SubVortex project in editable mode
echo "📚 Installing SubVortex project in editable mode..."
pip install -e ../../../

# Deactivate virtual environment
echo "🛑 Deactivating venv..."
deactivate

echo "✅ Validator Neuron setup completed successfully."
