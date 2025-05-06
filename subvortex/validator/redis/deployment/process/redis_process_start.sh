#!/bin/bash

set -euo pipefail

SERVICE_NAME="subvortex-validator-redis"
CONFIG_FILE="/etc/redis/redis.conf"
REDIS_CLI_CMD="redis-cli -a ${SUBVORTEX_REDIS_PASSWORD:-} -p ${SUBVORTEX_REDIS_PORT:-6379} PING"
REDIS_USER="redis"
REDIS_GROUP="redis"

echo "▶️ Starting $SERVICE_NAME via PM2 using config: $CONFIG_FILE"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Redis config not found at $CONFIG_FILE. Run setup.sh first."
    exit 1
fi

# Check if process is already managed by PM2
if pm2 describe "$SERVICE_NAME" >/dev/null 2>&1; then
    if pm2 status "$SERVICE_NAME" | grep -q "online"; then
        echo "🔁 $SERVICE_NAME is already running — reloading..."
        pm2 reload "$SERVICE_NAME" --update-env
    else
        echo "♻️ $SERVICE_NAME exists but not running — restarting..."
        pm2 restart "$SERVICE_NAME" --update-env
    fi
else
    echo "🚀 Starting $SERVICE_NAME via PM2 as $REDIS_USER:$REDIS_GROUP..."
    sudo pm2 start redis-server \
        --name "$SERVICE_NAME" \
        --uid "$REDIS_USER" \
        --gid "$REDIS_GROUP" \
        -- "$CONFIG_FILE" \
        --daemonize no
fi

echo "✅ Validator Redis is running and responsive."
