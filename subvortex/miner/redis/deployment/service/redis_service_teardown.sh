#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-miner-redis
PROJECT_WORKING_DIR="${SUBVORTEX_WORKING_DIR:-}"

# --- Basic Checks ---
if [[ "$EUID" -ne 0 ]]; then
  echo "🛑 Must be run as root. Re-running with sudo..."
  exec sudo "$0" "$@"
fi

echo "🧹 Starting $SERVICE_NAME teardown..."

# Fallback to script location if PROJECT_WORKING_DIR is not set
if [[ -z "$PROJECT_WORKING_DIR" ]]; then
  SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PROJECT_WORKING_DIR="$(realpath "$SCRIPT_PATH/../../../../../")"
  echo "📁 PROJECT_WORKING_DIR not set — using fallback: $PROJECT_WORKING_DIR"
else
  echo "📁 Using PROJECT_WORKING_DIR from environment: $PROJECT_WORKING_DIR"
fi

SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
SERVICE_WORKING_DIR="$PROJECT_WORKING_DIR/subvortex/miner/redis"
SERVICE_LOG_DIR="/var/log/subvortex-miner"
SERVICE_LOG_PREFIX="subvortex-miner-redis"

# Remove the service
echo "🔍 Checking $SERVICE_NAME..."
if [[ -f "$SERVICE_FILE" ]]; then
    echo "🚫 Disabling systemd service: $SERVICE_NAME..."
    systemctl disable "${SERVICE_NAME}.service" || true
    
    echo "🧹 Removing systemd service file..."
    rm -f "/etc/systemd/system/${SERVICE_NAME}.service"

    echo "🔄 Reloading systemd daemon..."
    systemctl daemon-reload
    systemctl reset-failed
else
    echo "ℹ️ $SERVICE_NAME is not running. No action needed."
fi

# Remove the service logs
echo "🔍 Cleaning logs for $SERVICE_NAME..."
if [[ -d "$SERVICE_LOG_DIR" ]]; then
    deleted_any=false
    shopt -s nullglob
    for file in "$SERVICE_LOG_DIR"/${SERVICE_LOG_PREFIX}*.log; do
        echo "🧹 Removing log file: $file"
        rm -f "$file"
        deleted_any=true
    done
    shopt -u nullglob

    if [[ "$deleted_any" = true ]]; then
        # Check if the directory is now empty
        if [[ -z "$(ls -A "$SERVICE_LOG_DIR")" ]]; then
            echo "🗑️  No logs left — removing empty directory: $SERVICE_LOG_DIR"
            rmdir "$SERVICE_LOG_DIR"
        else
            echo "📁 Some logs remain in $SERVICE_LOG_DIR — directory not removed."
        fi
    else
        echo "ℹ️ No log files found for prefix: $SERVICE_LOG_PREFIX"
    fi
else
    echo "ℹ️ Log directory $SERVICE_LOG_DIR does not exist. Skipping."
fi

# --- Package service cleanup ---
echo "📦 Removing package 'redis-server'..."

if command -v apt-get &> /dev/null; then
    sudo apt-get purge -y redis-server
    sudo apt-get autoremove -y
elif command -v dnf &> /dev/null; then
    sudo dnf remove -y redis-server
elif command -v pacman &> /dev/null; then
    sudo pacman -Rns --noconfirm redis-server
else
    echo "⚠️ Unsupported package manager. Please uninstall redis-server manually."
fi

# Clean up leftover binary if still present
REDIS_BIN=$(command -v redis-server 2>/dev/null || true)
if [[ -n "$REDIS_BIN" ]]; then
    echo "🧹 Removing leftover binary at $REDIS_BIN"
    sudo rm -f "$REDIS_BIN" || true
fi


echo "✅ $SERVICE_NAME uninstalled successfully."