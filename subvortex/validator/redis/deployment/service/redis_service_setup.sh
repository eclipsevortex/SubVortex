#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-validator-redis
PROJECT_WORKING_DIR="${SUBVORTEX_WORKING_DIR:-}"

if [[ "$EUID" -ne 0 ]]; then
  echo "🛑 Must be run as root. Re-running with sudo..."
  exec sudo "$0" "$@"
fi

echo "🔧 Starting $SERVICE_NAME setup..."

# Fallback to script location if PROJECT_WORKING_DIR is not set
if [[ -z "$PROJECT_WORKING_DIR" ]]; then
  SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PROJECT_WORKING_DIR="$(realpath "$SCRIPT_PATH/../../../../../")"
  echo "📁 PROJECT_WORKING_DIR not set — using fallback: $PROJECT_WORKING_DIR"
else
  echo "📁 Using PROJECT_WORKING_DIR from environment: $PROJECT_WORKING_DIR"
fi

SERVICE_WORKING_DIR="$PROJECT_WORKING_DIR/subvortex/validator/redis"

SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
SERVICE_TEMPLATE="$SERVICE_WORKING_DIR/deployment/templates/$SERVICE_NAME.service"
SERVICE_LOG_DIR="/var/log/subvortex-validator"
TEMP_SERVICE_FILE="/tmp/$SERVICE_NAME.service"

# --- Install binaries or create venv ---
# --- Package-based service setup ---
echo "📦 Installing package dependencies..."
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

# --- Look for config and copy if exists ---
CONFIG_DIR="$SERVICE_WORKING_DIR/deployment/templates"
DEST_CONFIG="/etc/redis/redis.conf"
for EXT in conf ini cfg; do
  CONFIG_FILE="$CONFIG_DIR/subvortex-validator-redis.$EXT"
  if [[ -f "$CONFIG_FILE" ]]; then
    echo "📄 Found config file: $CONFIG_FILE → copying to $DEST_CONFIG"
    cp "$CONFIG_FILE" "$DEST_CONFIG"
    break
  fi
done


echo "📁 Preparing log directory..."
mkdir -p "$SERVICE_LOG_DIR"
chown redis:redis "$SERVICE_LOG_DIR"

echo "📝 Preparing systemd service file from template..."
# Replace placeholder <WORKING_DIR> with actual path
sed "s|<WORKING_DIR>|$PROJECT_WORKING_DIR|g" "$SERVICE_TEMPLATE" > "$TEMP_SERVICE_FILE"

echo "📝 Installing systemd service file to $SERVICE_FILE..."
mv "$TEMP_SERVICE_FILE" "$SERVICE_FILE"

# --- Permissions and Reload ---
chmod 644 "$SERVICE_FILE"
systemctl daemon-reload

echo "✅ $SERVICE_NAME installed successfully."