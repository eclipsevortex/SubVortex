#!/bin/bash

set -euo pipefail

# Determine script directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

NEURON_NAME="subvortex-validator"
SERVICE_NAME="$NEURON_NAME-redis"
DEPLOY_TEMPLATES="./deployment/templates"
CONFIG_DEST="/etc/redis"
REDIS_CONF="$CONFIG_DEST/redis.conf"

# Load environment variables
echo "🔍 Loading environment variables from .env..."
export $(grep -v '^#' .env | xargs)

echo "📂 Preparing /etc/redis directory..."
sudo mkdir -p "$CONFIG_DEST"

echo "📂 Copying Redis config BEFORE installing redis-server..."
if [ ! -f "$DEPLOY_TEMPLATES/${SERVICE_NAME}.conf" ]; then
  echo "❌ Missing template: $DEPLOY_TEMPLATES/${SERVICE_NAME}.conf"
  exit 1
fi
sudo cp "$DEPLOY_TEMPLATES/${SERVICE_NAME}.conf" "$REDIS_CONF"
sudo chown root:root "$REDIS_CONF"

# 🔐 Inject Redis password if env variable is set
if [[ -n "${SUBVORTEX_REDIS_PASSWORD:-}" ]]; then
  echo "🔐 Injecting Redis password into redis.conf..."
  if grep -q "^requirepass" "$REDIS_CONF"; then
    sudo sed -i "s/^requirepass .*/requirepass $SUBVORTEX_REDIS_PASSWORD/" "$REDIS_CONF"
  else
    sudo sed -i "/^# requirepass/a requirepass $SUBVORTEX_REDIS_PASSWORD" "$REDIS_CONF"
  fi
else
  echo "⚠️ Environment variable SUBVORTEX_REDIS_PASSWORD is not set — skipping password injection."
fi

echo "📁 Preparing log directory..."
sudo mkdir -p "/var/log/$SERVICE_NAME"
sudo chown root:root "/var/log/$SERVICE_NAME"

echo "🚀 Installing Redis server if not already installed..."
if ! command -v redis-server >/dev/null; then
  sudo apt update
  sudo apt install -y -o Dpkg::Options::="--force-confold" redis-server
else
  echo "✅ redis-server already installed."
fi

echo "✅ Validator Redis setup completed successfully."
