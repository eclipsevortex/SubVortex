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

NEURON_NAME="subvortex-miner"
SERVICE_NAME="$NEURON_NAME-neuron"
PACKAGE_NAME="subvortex"

echo "📦 Starting Miner Neuron PM2 teardown..."

# Stop and delete the PM2 process
echo "🔍 Checking for PM2 process: $SERVICE_NAME..."
if pm2 describe "$SERVICE_NAME" >/dev/null 2>&1; then
    echo "🛑 Stopping PM2 process: $SERVICE_NAME..."
    pm2 stop "$SERVICE_NAME"
    
    echo "🗑️ Deleting PM2 process: $SERVICE_NAME..."
    pm2 delete "$SERVICE_NAME"
else
    echo "ℹ️ PM2 process $SERVICE_NAME not found. Skipping stop/delete."
fi

# Uninstall dependencies if virtual environment exists
echo "🔍 Checking for Python virtual environment..."
if [[ -d "venv" ]]; then
    echo "🐍 Activating virtual environment..."
    source "venv/bin/activate"
    
    if ./venv/bin/python -m pip list | grep -q "$PACKAGE_NAME"; then
        echo "📦 Uninstalling editable package: $PACKAGE_NAME..."
        ./venv/bin/python -m pip uninstall -y "$PACKAGE_NAME" || true
    else
        echo "ℹ️ Editable package $PACKAGE_NAME not found. Skipping."
    fi
    
    if [[ -f "requirements.txt" ]]; then
        echo "📚 Uninstalling dependencies from requirements.txt..."
        ./venv/bin/python -m pip uninstall -y -r "requirements.txt" || true
    else
        echo "⚠️ requirements.txt not found. Skipping dependency uninstallation."
    fi

    echo "🛑 Deactivating virtual environment..."
    deactivate

    echo "🧹 Removing virtual environment directory..."
    rm -rf "venv"
else
    echo "ℹ️ Virtual environment not found. Skipping removal."
fi

# Ensure egg-info is removed
echo "🧹 Checking for .egg-info directory..."
EGG_INFO_DIR=$(find . -name "*.egg-info" -type d)
if [[ -n "$EGG_INFO_DIR" ]]; then
    echo "🧹 Removing egg-info directory: $EGG_INFO_DIR..."
    rm -rf "$EGG_INFO_DIR"
else
    echo "ℹ️ No egg-info directory found. Skipping."
fi

echo "✅ Miner Neuron PM2 teardown completed successfully."