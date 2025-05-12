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

NEURON_NAME="subvortex-validator"
SERVICE_NAME="$NEURON_NAME-neuron"
PACKAGE_NAME="subvortex"

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

echo "📦 Starting Validator Neuron teardown..."

# Stop and disable the systemd service
echo "🔍 Checking for existing systemd service: $SERVICE_NAME..."
if systemctl list-units --type=service --all | grep -q "${SERVICE_NAME}.service"; then
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "🛑 Stopping systemd service: $SERVICE_NAME..."
        systemctl stop "${SERVICE_NAME}.service"
    fi
    
    echo "🚫 Disabling systemd service: $SERVICE_NAME..."
    systemctl disable "${SERVICE_NAME}.service"
    
    echo "🧹 Removing systemd service file..."
    rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
    
    echo "🔄 Reloading systemd daemon..."
    systemctl daemon-reexec
    systemctl daemon-reload
else
    echo "ℹ️ Systemd service ${SERVICE_NAME}.service not found. Skipping stop/disable."
fi

# Remove log directory
LOG_DIR="/var/log/$NEURON_NAME"
echo "🧹 Checking for log directory at $LOG_DIR..."
if [[ -d "$LOG_DIR" ]]; then
    echo "🧹 Removing log directory: $LOG_DIR"
    rm -rf "$LOG_DIR"
else
    echo "ℹ️ Log directory $LOG_DIR does not exist. Skipping."
fi

# Uninstall dependencies if virtual environment exists
echo "🔍 Checking for Python virtual environment..."
if [[ -d "venv" ]]; then
    echo "🐍 Activating virtual environment..."
    source "venv/bin/activate"
    
    if ./venv/bin/python -m pip list | grep -q "$PACKAGE_NAME"; then
        echo "📦 Uninstalling editable package: $PACKAGE_NAME..."
        ./venv/bin/python -m pip uninstall -y "$PACKAGE_NAME"|| true
    else
        echo "ℹ️ Editable package $PACKAGE_NAME not found. Skipping uninstall."
    fi
    
    if [[ -f "requirements.txt" ]]; then
        echo "📦 Uninstalling dependencies from requirements.txt..."
        ./venv/bin/python -m pip uninstall -y -r "requirements.txt"
    else
        echo "⚠️ requirements.txt not found. Skipping dependency uninstallation."
    fi
    
    echo "🛑 Deactivating virtual environment..."
    deactivate
    
    echo "🧹 Removing virtual environment directory..."
    rm -rf "venv"
else
    echo "ℹ️ Virtual environment not found. Skipping."
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

echo "✅ Validator Neuron teardown completed successfully."
