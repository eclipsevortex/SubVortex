#!/bin/bash

set -euo pipefail

# Ensure script run as root
if [[ "$EUID" -ne 0 ]]; then
    echo "🛑 This script must be run as root. Re-running with sudo..."
    exec sudo "$0" "$@"
fi

SERVICE_NAME="subvortex-validator-redis"

echo "🛑 Attempting to stop $SERVICE_NAME..."

# Check if the service is running before stopping
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "🔻 $SERVICE_NAME is currently running — stopping it now..."
    systemctl stop "$SERVICE_NAME"
    systemctl disable "$SERVICE_NAME"
else
    echo "ℹ️ $SERVICE_NAME is not running. No action needed."
fi

echo "✅ Validator Redis stopped successfully."
