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

# Load environment variables from .env safely
set -a
source .env
set +a

echo "🚀 Installing Redis server if not already installed..."
if ! command -v redis-server >/dev/null; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -o Dpkg::Options::="--force-confold" redis-server
else
  echo "✅ redis-server already installed."
fi

echo "🛑 Stopping and disabling default redis-server systemd service..."
sudo systemctl stop redis-server || true
sudo systemctl disable redis-server || true

echo "📂 Preparing /etc/redis directory..."
sudo mkdir -p "$CONFIG_DEST"

echo "📂 Copying Redis config BEFORE masking redis-server..."
if [ ! -f "$DEPLOY_TEMPLATES/${SERVICE_NAME}.conf" ]; then
  echo "❌ Missing template: $DEPLOY_TEMPLATES/${SERVICE_NAME}.conf"
  exit 1
fi
sudo cp "$DEPLOY_TEMPLATES/${SERVICE_NAME}.conf" "$CONFIG_DEST/redis.conf"
sudo chown root:root "$CONFIG_DEST/redis.conf"

# 🔐 Inject Redis password if env variable is set
if [[ -n "${SUBVORTEX_REDIS_PASSWORD:-}" ]]; then
  echo "🔐 Injecting Redis password into config..."
  if grep -q "^requirepass" "$CONFIG_DEST/redis.conf"; then
    sudo sed -i "s/^requirepass .*/requirepass $SUBVORTEX_REDIS_PASSWORD/" "$CONFIG_DEST/redis.conf"
  else
    sudo sed -i "/^# requirepass/a requirepass $SUBVORTEX_REDIS_PASSWORD" "$CONFIG_DEST/redis.conf"
  fi
else
  echo "⚠️ Environment variable SUBVORTEX_REDIS_PASSWORD is not set — skipping password injection."
fi

echo "📁 Preparing log directory..."
sudo mkdir -p /var/log/$NEURON_NAME
sudo chown root:root /var/log/$NEURON_NAME

echo "🚫 Masking redis-server systemd service to prevent default auto-start..."
sudo systemctl mask redis-server || true

echo "📂 Copying custom systemd service template for Validator Redis..."
if [ ! -f "$DEPLOY_TEMPLATES/${SERVICE_NAME}.service" ]; then
  echo "❌ Missing template: $DEPLOY_TEMPLATES/${SERVICE_NAME}.service"
  exit 1
fi
sudo cp "$DEPLOY_TEMPLATES/${SERVICE_NAME}.service" "$SYSTEMD_DEST/${SERVICE_NAME}.service"

echo "🔧 Reloading systemd daemon..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

echo "✅ Validator Redis setup completed successfully."
