#!/bin/bash

set -e

SERVICE_NAME=subvortex-validator-neuron
PACKAGE_NAME=subvortex

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Stop and delete the validator process
if pm2 list | grep -q "$SERVICE_NAME"; then
    echo "Stopping PM2 process $SERVICE_NAME..."
    
    # Stop the api
    pm2 stop $SERVICE_NAME
    
    # Delete the api
    pm2 delete $SERVICE_NAME
fi

echo $SCRIPT_DIR

ls .

# Uninstall dependencies if virtual environment exists
if [[ -d "venv" ]]; then
    echo "Activating virtual environment to uninstall dependencies..."
    source "venv/bin/activate"
    
    if pip list | grep -q "$PACKAGE_NAME"; then
        echo "Uninstalling editable package: $PACKAGE_NAME..."
        pip uninstall -y "$PACKAGE_NAME"
    else
        echo "Editable package $PACKAGE_NAME not found. Skipping."
    fi
    
    # Uninstall dependencies
    if [[ -f "requirements.txt" ]]; then
        echo "Uninstalling dependencies..."
        pip uninstall -y -r "requirements.txt"
    else
        echo "requirements.txt not found. Skipping dependency uninstallation."
    fi
    
    # Deactivate virtual environment
    deactivate
    
    echo "Removing virtual environment..."
    rm -rf "venv"
else
    echo "Virtual environment not found. Skipping removal."
fi

# Ensure egg-info is removed
EGG_INFO_DIR=$(find . -name "*.egg-info" -type d)
if [[ -n "$EGG_INFO_DIR" ]]; then
    echo "Removing egg-info directory: $EGG_INFO_DIR..."
    rm -rf "$EGG_INFO_DIR"
else
    echo "No egg-info directory found."
fi

echo "✅ Validator teardown completed successfully."
