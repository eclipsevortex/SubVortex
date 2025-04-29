#!/bin/bash

set -euo pipefail

# Determine script directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

NEURON_NAME="subvortex-validator"
SERVICE_NAME="$NEURON_NAME-redis"
CONFIG_DEST="/etc/redis"
REDIS_CONF="$CONFIG_DEST/redis.conf"
LOG_DIR="/var/log/$SERVICE_NAME"

echo "📦 Starting Validator Redis teardown for PM2 setup..."

# Load environment variables
echo "🔍 Loading environment variables from .env..."
export $(grep -v '^#' .env | xargs)

# Stop and delete PM2 process if running
echo "🛑 Stopping and deleting PM2 process if it exists..."
if pm2 list | grep -q "$SERVICE_NAME"; then
    pm2 stop "$SERVICE_NAME" || true
    pm2 delete "$SERVICE_NAME" || true
    echo "✅ PM2 process $SERVICE_NAME removed."
else
    echo "ℹ️ No PM2 process found for $SERVICE_NAME."
fi

# Remove redis.conf
echo "🧹 Removing Redis config file at $REDIS_CONF..."
if [ -f "$REDIS_CONF" ]; then
    sudo rm -f "$REDIS_CONF"
    echo "✅ Redis config file removed."
else
    echo "ℹ️ Redis config file not found — skipping."
fi

# Remove /var/log directory
echo "🧹 Removing Redis log directory at $LOG_DIR..."
if [ -d "$LOG_DIR" ]; then
    sudo rm -rf "$LOG_DIR"
    echo "✅ Redis log directory removed."
else
    echo "ℹ️ Redis log directory not found — skipping."
fi

# Remove /etc/redis folder if empty
if [ -d "$CONFIG_DEST" ] && [ -z "$(ls -A "$CONFIG_DEST")" ]; then
    echo "🧹 /etc/redis is empty, removing..."
    sudo rmdir "$CONFIG_DEST"
    echo "✅ /etc/redis directory removed."
else
    echo "ℹ️ /etc/redis not empty or not found — skipping removal."
fi

# Uninstall redis-server if installed
echo "🔍 Checking if redis-server is installed..."
if command -v redis-server >/dev/null 2>&1; then
    echo "🧨 redis-server is installed. Uninstalling..."
    sudo apt purge -y redis-server
    sudo apt autoremove -y
    echo "✅ redis-server uninstalled."
else
    echo "ℹ️ redis-server not installed — nothing to uninstall."
fi

echo "✅ Validator Redis teardown completed successfully."