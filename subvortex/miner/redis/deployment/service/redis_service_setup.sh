#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-miner-redis
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

SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
SERVICE_WORKING_DIR="$PROJECT_WORKING_DIR/subvortex/miner/redis"
SERVICE_TEMPLATE="$SERVICE_WORKING_DIR/deployment/templates/$SERVICE_NAME.service"
SERVICE_LOG_DIR="/var/log/subvortex-miner"
TEMP_SERVICE_FILE="/tmp/$SERVICE_NAME.service"

# --- Package-based service setup ---
echo "📦 Installing package dependencies..."
if command -v apt-get &> /dev/null; then
  echo "🧹 Removing Redis Labs repository (if present)..."
  sudo rm -f /etc/apt/sources.list.d/redis.list
  sudo rm -f /etc/apt/trusted.gpg.d/redis-archive-keyring.gpg

  echo "🧹 Cleaning APT cache and redis-server .deb files..."
  sudo apt-get clean
  sudo rm -f /var/cache/apt/archives/redis-server_*.deb || true
  sudo apt-get update

  echo "📌 Installing redis-server from Ubuntu repo..."
  sudo apt-get install --allow-downgrades -y redis-server

elif command -v dnf &> /dev/null; then
  echo "🧹 Removing Redis Labs repo from DNF (if present)..."
  sudo rm -f /etc/yum.repos.d/redis.repo || true

  echo "🧹 Cleaning DNF metadata and cache..."
  sudo dnf clean all
  sudo dnf makecache
  sudo dnf install -y redis-server

elif command -v pacman &> /dev/null; then
  echo "🧹 Cleaning Pacman cache for redis-server..."
  sudo pacman -Scc --noconfirm || true
  sudo pacman -Sy --noconfirm redis-server

else
  echo "⚠️ Unsupported package manager. Please install redis-server manually."
fi

# --- Stop and mask default service to avoid conflict ---
if systemctl list-unit-files --quiet "redis-server.service"; then
  if systemctl is-active --quiet "redis-server.service"; then
    echo "🛑 Stopping running service: redis-server.service"
    systemctl stop "redis-server.service"
  fi
  echo "🚫 Masking redis-server.service"
  systemctl mask "redis-server.service"
fi

# --- Promote and patch system unit to /etc/systemd/system ---
CUSTOM_UNIT_PATH="/etc/systemd/system/$SERVICE_NAME.service"

# Prefer vendor-provided unit file from /lib/systemd/system
if [[ -f "/lib/systemd/system/redis-server.service" ]]; then
  BASE_UNIT_PATH="/lib/systemd/system/redis-server.service"
else
  BASE_UNIT_PATH=$(systemctl show -p FragmentPath redis-server.service | cut -d= -f2)
fi

if [[ -n "$BASE_UNIT_PATH" && -e "$BASE_UNIT_PATH" ]]; then
  echo "📄 Found base unit at: $BASE_UNIT_PATH"
  echo "📄 Copying to: $CUSTOM_UNIT_PATH"
  cp "$BASE_UNIT_PATH" "$CUSTOM_UNIT_PATH"

  echo "✏️ Patching Description and Alias"
  sed -i "s|^Description=.*|Description=SubVortex Miner Redis|" "$CUSTOM_UNIT_PATH"

  if grep -q "^Alias=" "$CUSTOM_UNIT_PATH"; then
    sed -i "s|^Alias=.*|Alias=$SERVICE_NAME.service|" "$CUSTOM_UNIT_PATH"
  else
    echo "Alias=$SERVICE_NAME.service" >> "$CUSTOM_UNIT_PATH"
  fi

  echo "✏️ Replacing PIDFile with /run/redis-server..pid"
  if grep -q "^PIDFile=" "$CUSTOM_UNIT_PATH"; then
    sed -i "s|^PIDFile=.*|PIDFile=/run/redis-server..pid|" "$CUSTOM_UNIT_PATH"
  else
    echo "PIDFile=/var/run/redis-server..pid" >> "$CUSTOM_UNIT_PATH"
  fi

  echo "✏️ Replacing ReadWritePaths inline"
  awk '
    BEGIN {
      replaced = 0;
      replacement = "ReadWritePaths=-/var/lib/redis -/var/log/redis -/run/redis -/var/log/subvortex-miner";
    }
    /^ReadWritePaths=/ {
      if (!replaced) {
        print replacement;
        replaced = 1;
      }
      next;
    }
    { print }
  ' "$CUSTOM_UNIT_PATH" > "$CUSTOM_UNIT_PATH.tmp" && mv "$CUSTOM_UNIT_PATH.tmp" "$CUSTOM_UNIT_PATH"

  chmod 644 "$CUSTOM_UNIT_PATH"
else
  echo "⚠️ Could not locate base unit file for redis-server.service"
fi

# --- Handle optional configuration templates ---
CONFIG_DIR="$SERVICE_WORKING_DIR/deployment/templates"

TEMPLATE_FILE="$CONFIG_DIR/subvortex-miner-redis.conf"
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
    sed -i "s|^logfile[[:space:]]*.*|logfile /var/log/subvortex-miner/subvortex-miner-redis.log|" "$DEST_FILE"
  else
    echo "logfile /var/log/subvortex-miner/subvortex-miner-redis.log" >> "$DEST_FILE"
  fi
else
  echo "🛑 Destination file $DEST_FILE does not exist — cannot apply overrides"
fi


echo "📁 Preparing log directory..."
mkdir -p "$SERVICE_LOG_DIR"
chown redis:redis "$SERVICE_LOG_DIR"

# --- Create log files and adjust permissions ---
LOG_PREFIX="$SERVICE_LOG_DIR/subvortex-miner-redis"
echo "🔒 Adjusting permissions for logs with prefix: $LOG_PREFIX"

# Ensure the log directory exists
mkdir -p "$(dirname "$LOG_PREFIX")"

# Create the log files if they don't exist
touch "${LOG_PREFIX}.log" "${LOG_PREFIX}-error.log"

# Set correct ownership
chown redis:redis "${LOG_PREFIX}.log" "${LOG_PREFIX}-error.log"

echo "ℹ️ Skipping systemd service file generation (generate_unit=false)"

echo "🔄 Reloading systemd and completing setup..."
systemctl daemon-reexec
systemctl daemon-reload

echo "✅ $SERVICE_NAME installed successfully."