#!/bin/bash

set -euo pipefail

NEURON_NAME="subvortex-validator"
SERVICE_NAME="$NEURON_NAME-neuron"
PACKAGE_NAME="subvortex"

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

echo "📦 Starting Validator Neuron PM2 teardown..."

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
    
    if pip list | grep -q "$PACKAGE_NAME"; then
        echo "📦 Uninstalling editable package: $PACKAGE_NAME..."
        pip uninstall -y "$PACKAGE_NAME"
    else
        echo "ℹ️ Editable package $PACKAGE_NAME not found. Skipping."
    fi
    
    if [[ -f "requirements.txt" ]]; then
        echo "📚 Uninstalling dependencies from requirements.txt..."
        pip uninstall -y -r "requirements.txt"
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

echo "✅ Validator Neuron PM2 teardown completed successfully."