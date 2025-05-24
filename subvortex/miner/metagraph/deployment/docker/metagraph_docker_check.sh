#!/bin/bash

set -euo pipefail

CONTAINER_NAME=subvortex-miner-metagraph
RESTART_THRESHOLD=3  # You can adjust this threshold

echo "🔍 Checking status of Docker container $CONTAINER_NAME..."


# Check if the container exists
if docker ps -a --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
    STATUS=$(docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME")
    RESTARTS=$(docker inspect -f '{{.RestartCount}}' "$CONTAINER_NAME")

    echo "ℹ️ Status: $STATUS"
    echo "🔁 Restart count: $RESTARTS"

    # Check restart threshold
    if [[ "$RESTARTS" -ge "$RESTART_THRESHOLD" ]]; then
        echo "⚠️ $CONTAINER_NAME has restarted $RESTARTS times — this may indicate a problem."
    fi

    if [[ "$STATUS" == "running" ]]; then
        echo "✅ $CONTAINER_NAME is currently running. Proceeding to stop..."
        docker stop "$CONTAINER_NAME"
        echo "🛑 $CONTAINER_NAME stopped successfully."
    else
        echo "⚠️ $CONTAINER_NAME is not currently running (status: $STATUS). No stop action needed."
    fi
else
    echo "ℹ️ Docker container $CONTAINER_NAME does not exist."
fi
