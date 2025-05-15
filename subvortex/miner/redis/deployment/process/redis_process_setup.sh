#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-miner-redis
PROJECT_WORKING_DIR="${SUBVORTEX_WORKING_DIR:-}"

echo "🔧 Starting $SERVICE_NAME setup..."

# Fallback to script location if PROJECT_WORKING_DIR is not set
if [[ -z "$PROJECT_WORKING_DIR" ]]; then
  SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PROJECT_WORKING_DIR="$(realpath "$SCRIPT_PATH/../../../../../")"
  echo "📁 PROJECT_WORKING_DIR not set — using fallback: $PROJECT_WORKING_DIR"
else
  echo "📁 Using PROJECT_WORKING_DIR from environment: $PROJECT_WORKING_DIR"
fi

SERVICE_WORKING_DIR="$PROJECT_WORKING_DIR/subvortex/miner/redis"

# --- Package-based service setup  ---
echo "📦 Installing package dependencies..."
# Replace with specific install commands if needed
# Example: apt-get install -y redis-server
if command -v apt-get &> /dev/null; then
  sudo apt-get update
  sudo apt-get install -y redis-server
elif command -v dnf &> /dev/null; then
  sudo dnf install -y redis-server
elif command -v pacman &> /dev/null; then
  sudo pacman -Sy --noconfirm redis-server
else
  echo "⚠️ Unsupported package manager. Install redis-server manually."
fi

# --- If a systemd unit for the package is running, stop and mask it ---
if systemctl list-units --type=service --all | grep -q "redis-server.service"; then
  if systemctl is-active --quiet "redis-server.service"; then
    echo "🛑 Stopping running systemd service: redis-server.service"
    sudo systemctl stop "redis-server.service"
  fi
  echo "🚫 Masking systemd service to prevent autostart: redis-server.service"
  sudo systemctl mask "redis-server.service"
else
  echo "ℹ️ No active systemd service found for redis-server.service"
fi

# Ensure logs to stdout/stderr
SERVICE_CONF_FILE="/etc/redis/redis.conf"
echo "📄 Forcing logfile to stdout/stderr (logfile \"\")..."
if grep -qE '^\s*logfile\s+' "$SERVICE_CONF_FILE"; then
    sudo sed -i 's|^\s*logfile\s\+.*|logfile ""|' "$SERVICE_CONF_FILE"
elif grep -q "^# *logfile" "$SERVICE_CONF_FILE"; then
    sudo sed -i '/^# *logfile/a logfile ""' "$SERVICE_CONF_FILE"
else
    echo 'logfile ""' | sudo tee -a "$SERVICE_CONF_FILE" > /dev/null
fi



echo "✅ $SERVICE_NAME installed successfully."