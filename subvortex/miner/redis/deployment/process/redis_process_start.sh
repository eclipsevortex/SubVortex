#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-miner-redis
PROJECT_WORKING_DIR="${SUBVORTEX_WORKING_DIR:-}"

echo "🚀 Starting $SERVICE_NAME..."

# Fallback to script location if PROJECT_WORKING_DIR is not set
if [[ -z "$PROJECT_WORKING_DIR" ]]; then
  SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PROJECT_WORKING_DIR="$(realpath "$SCRIPT_PATH/../../../../../")"
  echo "📁 PROJECT_WORKING_DIR not set — using fallback: $PROJECT_WORKING_DIR"
else
  echo "📁 Using PROJECT_WORKING_DIR from environment: $PROJECT_WORKING_DIR"
fi

SERVICE_WORKING_DIR="$PROJECT_WORKING_DIR/subvortex/miner/redis"

echo "🔍 Checking $SERVICE_NAME..."
if pm2 describe "$SERVICE_NAME" >/dev/null 2>&1; then
    if pm2 status "$SERVICE_NAME" | grep -q "online"; then
        echo "🔁 $SERVICE_NAME is already running — reloading..."
        pm2 reload "$SERVICE_NAME" --update-env
    else
        echo "♻️ $SERVICE_NAME exists but not running — restarting..."
        pm2 restart "$SERVICE_NAME" --update-env
    fi
else
    echo "🚀 Starting $SERVICE_NAME as redis:redis..."
    sudo pm2 start redis-server \
        --name "$SERVICE_NAME" \
        --uid "redis" \
        --gid "redis" \
        -- "/etc/redis/redis.conf" \
        --daemonize no
fi


echo "✅ $SERVICE_NAME started successfully."