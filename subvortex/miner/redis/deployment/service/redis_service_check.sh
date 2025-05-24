#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-miner-redis.service
RESTART_THRESHOLD=3  # You can adjust this threshold

echo "🔍 Checking status of $SERVICE_NAME..."

# Check if the service exists
if systemctl list-units --type=service --all | grep -q "$SERVICE_NAME"; then
    STATUS=$(systemctl is-active "$SERVICE_NAME")
    RESTARTS=$(systemctl show "$SERVICE_NAME" -p NRestarts | cut -d= -f2)

    echo "ℹ️ Status: $STATUS"
    echo "🔁 Restart count: $RESTARTS"

    # Check restart threshold
    if [[ "$RESTARTS" -ge "$RESTART_THRESHOLD" ]]; then
        echo "⚠️ $SERVICE_NAME has restarted $RESTARTS times — this may indicate a problem."
    fi

    if [[ "$STATUS" == "active" ]]; then
        echo "✅ $SERVICE_NAME is currently running. Proceeding to stop..."
        sudo systemctl stop "$SERVICE_NAME"
        echo "🛑 $SERVICE_NAME stopped successfully."
    else
        echo "⚠️ $SERVICE_NAME is not currently running. No stop action needed."
    fi
else
    echo "ℹ️ $SERVICE_NAME does not exist or is not managed by systemd."
fi