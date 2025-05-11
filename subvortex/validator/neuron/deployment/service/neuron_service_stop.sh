#!/bin/bash

set -euo pipefail

# Ensure script run as root
if [[ "$EUID" -ne 0 ]]; then
    echo "🛑 This script must be run as root. Re-running with sudo..."
    exec sudo "$0" "$@"
fi

SERVICE_NAME="subvortex-validator-neuron"

echo "🔍 Checking $SERVICE_NAME status..."

# Check if the service is active
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "🛑 $SERVICE_NAME is currently running — stopping it now..."
    systemctl stop "$SERVICE_NAME"
    echo "✅ $SERVICE_NAME stopped successfully."
else
    echo "ℹ️ $SERVICE_NAME is not running. No action needed."
fi

echo "✅ Validator Neuron stopped successfully."