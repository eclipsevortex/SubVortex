#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-miner-neuron
RESTART_THRESHOLD=3  # You can adjust this threshold

echo "🔍 Checking status of $SERVICE_NAME..."

# Check if the service is managed by PM2
if pm2 list | grep -q "$SERVICE_NAME"; then
    STATUS=$(pm2 info "$SERVICE_NAME" | grep "status" | awk '{print $4}')
    RESTARTS=$(pm2 info "$SERVICE_NAME" | grep "restart" | awk '{print $4}')

    echo "ℹ️ Status: $STATUS"
    echo "🔁 Restart count: $RESTARTS"

    # Check restart threshold
    if [[ "$RESTARTS" -ge "$RESTART_THRESHOLD" ]]; then
        echo "⚠️ $SERVICE_NAME has restarted $RESTARTS times — this may indicate a problem."
    fi

    if [[ "$STATUS" == "online" ]]; then
        echo "✅ $SERVICE_NAME is currently running. Proceeding to stop..."
        pm2 stop "$SERVICE_NAME"
        echo "🛑 $SERVICE_NAME stopped successfully."
    else
        echo "⚠️ $SERVICE_NAME is listed but not online (status: $STATUS). No stop action needed."
    fi
else
    echo "ℹ️ $SERVICE_NAME is not running under PM2. No action needed."
fi