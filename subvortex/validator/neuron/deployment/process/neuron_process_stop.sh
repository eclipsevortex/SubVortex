#!/bin/bash

set -euo pipefail

SERVICE_NAME="subvortex-validator-neuron"

echo "🔍 Checking PM2 process: $SERVICE_NAME..."

# Check if PM2 process is running and stop it
if pm2 describe "$SERVICE_NAME" >/dev/null 2>&1; then
    echo "🛑 $SERVICE_NAME is currently running — stopping it..."
    pm2 stop "$SERVICE_NAME"
    echo "✅ $SERVICE_NAME stopped successfully."
else
    echo "ℹ️ $SERVICE_NAME is not running. No action needed."
fi

echo "✅ Validator Neuron PM2 process stop completed successfully."
