#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-validator-redis
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

SERVICE_WORKING_DIR="$PROJECT_WORKING_DIR/subvortex/validator/redis"

# --- Load environment variables from .env file ---
ENV_FILE="$SERVICE_WORKING_DIR/.env"

if [[ -f "$ENV_FILE" ]]; then
  echo "🌱 Loading environment variables from $ENV_FILE"
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
else
  echo "⚠️ No .env file found at $ENV_FILE"
fi

echo "🔧 Running provision install hook..."
bash "$SERVICE_WORKING_DIR/deployment/provision/redis_server_install.sh"

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

# --- Handle optional configuration templates ---
CONFIG_DIR="$SERVICE_WORKING_DIR/deployment/templates"

TEMPLATE_FILE="$CONFIG_DIR/subvortex-validator-redis.conf"
DEST_FILE="/etc/redis/redis.conf"

if [[ -f "$TEMPLATE_FILE" ]]; then
  echo "📄 Found template: $TEMPLATE_FILE → copying to $DEST_FILE"
  cp "$TEMPLATE_FILE" "$DEST_FILE"
else
  echo "⚠️ Template not found: $TEMPLATE_FILE — will attempt to patch $DEST_FILE if it exists"
fi

if [[ -f "$DEST_FILE" ]]; then
  echo "🔧 Applying overrides to $DEST_FILE"
  if grep -q "^logfile\s*" "$DEST_FILE"; then
    sed -i "s|^logfile[[:space:]]*.*|logfile \"\"|" "$DEST_FILE"
  else
    echo "logfile \"\"" >> "$DEST_FILE"
  fi
  if grep -q "^requirepass\s*" "$DEST_FILE"; then
    sed -i "s|^requirepass[[:space:]]*.*|requirepass ${SUBVORTEX_REDIS_PASSWORD:-\"\"}|" "$DEST_FILE"
  else
    echo "requirepass ${SUBVORTEX_REDIS_PASSWORD:-\"\"}" >> "$DEST_FILE"
  fi
else
  echo "🛑 Destination file $DEST_FILE does not exist — cannot apply overrides"
fi



echo "✅ $SERVICE_NAME installed successfully."