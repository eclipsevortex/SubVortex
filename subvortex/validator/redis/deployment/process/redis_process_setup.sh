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
CHECKSUM_DIR="/var/lib/subvortex/${SERVICE_NAME}-checksums"

# Load environment variables
echo "🔍 Loading environment variables from .env..."
set -a
source .env
set +a

# Ensure checksum directory exists
sudo mkdir -p "$CHECKSUM_DIR"

compute_checksum() {
    sha256sum "$1" | awk '{print $1}'
}

store_checksum() {
    local content="$1"
    local name="$2"
    echo -n "$content" | sha256sum | awk '{print $1}' | sudo tee "$CHECKSUM_DIR/$name" >/dev/null
}

checksum_changed() {
    local file="$1"
    local name="$2"
    local new_hash
    new_hash=$(compute_checksum "$file")
    if [[ ! -f "$CHECKSUM_DIR/$name" ]] || [[ "$new_hash" != "$(cat "$CHECKSUM_DIR/$name")" ]]; then
        echo "$new_hash" | sudo tee "$CHECKSUM_DIR/$name" >/dev/null
        return 0
    fi
    return 1
}

value_changed() {
    local value="$1"
    local name="$2"
    local new_hash
    new_hash=$(echo -n "$value" | sha256sum | awk '{print $1}')
    if [[ ! -f "$CHECKSUM_DIR/$name" ]] || [[ "$new_hash" != "$(cat "$CHECKSUM_DIR/$name")" ]]; then
        echo "$new_hash" | sudo tee "$CHECKSUM_DIR/$name" >/dev/null
        return 0
    fi
    return 1
}

echo "📂 Preparing $CONFIG_DEST directory..."
sudo mkdir -p "$CONFIG_DEST"

TEMPLATE_CONF="$DEPLOY_TEMPLATES/${SERVICE_NAME}.conf"
if [[ ! -f "$TEMPLATE_CONF" ]]; then
  echo "❌ Missing template: $TEMPLATE_CONF"
  exit 1
fi

checksum_changed "$TEMPLATE_CONF" "redis.conf.template" && CONF_CHANGED=true || CONF_CHANGED=false

if [[ -n "${SUBVORTEX_REDIS_PASSWORD:-}" ]]; then
  value_changed "$SUBVORTEX_REDIS_PASSWORD" "redis.password" && PASS_CHANGED=true || PASS_CHANGED=false
else
  PASS_CHANGED=false
fi

if [[ "$CONF_CHANGED" == true || "$PASS_CHANGED" == true ]]; then
  echo "📝 Changes detected — updating redis.conf..."
  sudo cp "$TEMPLATE_CONF" "$REDIS_CONF"
  sudo chown root:root "$REDIS_CONF"

  if [[ -n "${SUBVORTEX_REDIS_PASSWORD:-}" ]]; then
    echo "🔐 Injecting password into redis.conf..."
    if grep -q "^requirepass" "$REDIS_CONF"; then
      sudo sed -i "s/^requirepass .*/requirepass $SUBVORTEX_REDIS_PASSWORD/" "$REDIS_CONF"
    else
      sudo sed -i "/^# requirepass/a requirepass $SUBVORTEX_REDIS_PASSWORD" "$REDIS_CONF"
    fi
  fi
else
  echo "✅ No config or password changes detected — skipping redis.conf update."
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

echo "✅ Validator Redis setup completed successfully (PM2-compatible)."
