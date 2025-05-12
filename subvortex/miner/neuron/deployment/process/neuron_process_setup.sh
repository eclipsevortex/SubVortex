#!/bin/bash

set -euo pipefail

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

echo "📦 Starting Miner Neuron setup..."

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🚀 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
if [[ -f "requirements.txt" ]]; then
    echo "📚 Installing Python dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found. Skipping dependency installation."
fi

# Ensure pyproject.toml is present (local execution only)
if [[ ! -f "../../../pyproject.toml" ]]; then
    if [[ -f "../../../pyproject-miner.toml" ]]; then
        echo "📄 pyproject.toml not found, copying pyproject-miner.toml..."
        cp ../../../pyproject-miner.toml ../../../pyproject.toml
    else
        echo "❌ pyproject.toml and pyproject-miner.toml both not found. Cannot proceed."
        exit 1
    fi
fi

# Install SubVortex in Editable Mode
echo "📚 Installing SubVortex package in editable mode..."
pip install -e ../../../

# Deactivate virtual environment
echo "🛑 Deactivating virtual environment..."
deactivate

echo "✅ Miner Neuron setup completed successfully."
