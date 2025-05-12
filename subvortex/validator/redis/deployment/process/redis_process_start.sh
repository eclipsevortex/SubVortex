#!/bin/bash

set -euo pipefail

# Determine working directory: prefer SUBVORTEX_WORKING_DIR, fallback to script location
SCRIPT_DIR="$(cd "$(dirname "$(python3 -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$0")")" && pwd)"

# Find project root by walking up until LICENSE is found
find_project_root() {
    local dir="$1"
    while [[ "$dir" != "/" ]]; do
        [[ -f "$dir/LICENSE" ]] && { echo "$dir"; return; }
        dir="$(dirname "$dir")"
    done
    return 1
}

PROJECT_ROOT="$(find_project_root "$SCRIPT_DIR")" || {
    echo "❌ Could not detect project root (LICENSE not found)"
    exit 1
}

# Resolve final working directory
if [[ -n "${SUBVORTEX_WORKING_DIR:-}" ]]; then
    REL_PATH="${SCRIPT_DIR#$PROJECT_ROOT/}"
    TARGET_DIR="$SUBVORTEX_WORKING_DIR/$REL_PATH"
    [[ -d "$TARGET_DIR" ]] || { echo "❌ Target directory does not exist: $TARGET_DIR"; exit 1; }
    echo "📁 Using SUBVORTEX_WORKING_DIR: $TARGET_DIR"
    cd "$TARGET_DIR"
else
    echo "📁 Using fallback PROJECT_ROOT: $SCRIPT_DIR"
    cd "$SCRIPT_DIR"
fi

echo "📍 Working directory: $(pwd)"

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
