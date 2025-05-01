#!/bin/bash

set -euo pipefail

# Determine script directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

NEURON_NAME=subvortex-validator
SERVICE_NAME="$NEURON_NAME-redis"
DEPLOY_TEMPLATES="./deployment/templates"
CONFIG_DEST="/etc/redis"
SYSTEMD_DEST="/etc/systemd/system"
REDIS_CONF="$CONFIG_DEST/redis.conf"
SYSTEMD_UNIT="$SYSTEMD_DEST/${SERVICE_NAME}.service"
CHECKSUM_DIR="/var/tmp/dumps/redis/${SERVICE_NAME}-checksums"

# Load environment variables from .env safely
set -a
source .env
set +a

mkdir -p "$CHECKSUM_DIR"

compute_checksum() {
    sha256sum "$1" | awk '{print $1}'
}

checksum_changed() {
    local file="$1"
    local name="$2"
    local new_hash
    new_hash=$(compute_checksum "$file")
    if [[ ! -f "$CHECKSUM_DIR/$name" ]] || [[ "$new_hash" != "$(cat "$CHECKSUM_DIR/$name")" ]]; then
        echo "$new_hash" > "$CHECKSUM_DIR/$name"
        return 0
    fi
    return 1
}

echo "🚀 Installing Redis server if not already installed..."
if ! command -v redis-server >/dev/null; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -o Dpkg::Options::="--force-confold" redis-server
else
  echo "✅ redis-server already installed."
fi

# Checksum redis binary
REDIS_BINARY="$(command -v redis-server)"
checksum_changed "$REDIS_BINARY" "redis-server.binary" && REDIS_CHANGED=true || REDIS_CHANGED=false

echo "📂 Preparing /etc/redis directory..."
sudo mkdir -p "$CONFIG_DEST"

echo "📂 Checking Redis config template..."
TEMPLATE_CONF="$DEPLOY_TEMPLATES/${SERVICE_NAME}.conf"
if [[ ! -f "$TEMPLATE_CONF" ]]; then
  echo "❌ Missing template: $TEMPLATE_CONF"
  exit 1
fi

checksum_changed "$TEMPLATE_CONF" "redis.conf.template" && CONF_CHANGED=true || CONF_CHANGED=false

if [[ "$REDIS_CHANGED" == true || "$CONF_CHANGED" == true ]]; then
  echo "📦 Changes detected — stopping service and preparing for upgrade..."
  echo "📤 Dumping Redis data..."
  redis-cli -a "${SUBVORTEX_REDIS_PASSWORD:-}" SAVE || echo "⚠️ Could not save Redis data."

  echo "🛑 Stopping and disabling default redis-server systemd service..."
  sudo systemctl stop redis-server || true
  sudo systemctl disable redis-server || true

  echo "📄 Installing updated redis.conf..."
  sudo cp "$TEMPLATE_CONF" "$REDIS_CONF"
  sudo chown root:root "$REDIS_CONF"
else
  echo "✅ No redis binary or config changes detected — skipping redis.conf update."
fi

# 🔐 Inject Redis password only if needed
if [[ -n "${SUBVORTEX_REDIS_PASSWORD:-}" ]]; then
  current_pass=$(grep -E '^\s*requirepass\s+' "$REDIS_CONF" | awk '{print $2}' || true)
  if [[ "$current_pass" != "$SUBVORTEX_REDIS_PASSWORD" ]]; then
    echo "🔐 Injecting or updating Redis password in redis.conf..."
    if grep -qE '^\s*requirepass\s+' "$REDIS_CONF"; then
      sudo sed -i "s|^\s*requirepass\s\+.*|requirepass $SUBVORTEX_REDIS_PASSWORD|" "$REDIS_CONF"
    elif grep -q "^# *requirepass" "$REDIS_CONF"; then
      sudo sed -i "/^# *requirepass/a requirepass $SUBVORTEX_REDIS_PASSWORD" "$REDIS_CONF"
    else
      echo "requirepass $SUBVORTEX_REDIS_PASSWORD" | sudo tee -a "$REDIS_CONF" > /dev/null
    fi
  else
    echo "🔐 Redis password already up-to-date — no changes made."
  fi
else
  echo "⚠️ Environment variable SUBVORTEX_REDIS_PASSWORD is not set — skipping password injection."
fi

echo "📁 Preparing log directory..."
sudo mkdir -p "/var/log/$NEURON_NAME"
sudo chown root:root "/var/log/$NEURON_NAME"

echo "🚫 Masking default redis-server systemd service..."
sudo systemctl mask redis-server || true

echo "📂 Checking systemd service template..."
TEMPLATE_SERVICE="$DEPLOY_TEMPLATES/${SERVICE_NAME}.service"
if [[ ! -f "$TEMPLATE_SERVICE" ]]; then
  echo "❌ Missing template: $TEMPLATE_SERVICE"
  exit 1
fi

checksum_changed "$TEMPLATE_SERVICE" "systemd.unit.template" && UNIT_CHANGED=true || UNIT_CHANGED=false

if [[ "$UNIT_CHANGED" == true ]]; then
  echo "📄 Installing updated systemd unit file..."
  sudo cp "$TEMPLATE_SERVICE" "$SYSTEMD_UNIT"
else
  echo "✅ No systemd unit changes detected — skipping unit update."
fi

# Create Redis working directory if specified in redis.conf
REDIS_DATA_DIR=$(grep -E '^\s*dir\s+' "$REDIS_CONF" | awk '{print $2}')
if [[ -n "$REDIS_DATA_DIR" ]]; then
  echo "📁 Ensuring Redis data directory exists: $REDIS_DATA_DIR"
  sudo mkdir -p "$REDIS_DATA_DIR"
  sudo chown root:root "$REDIS_DATA_DIR"
else
  echo "⚠️ Could not determine Redis data directory from redis.conf."
fi

echo "🔧 Reloading systemd daemon..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

echo "✅ Validator Redis setup completed successfully."
