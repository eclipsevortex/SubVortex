#!/bin/bash

set -euo pipefail

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

NEURON_NAME="subvortex-validator"
SERVICE_NAME="$NEURON_NAME-redis"
REDIS_CONF="./deployment/templates/$SERVICE_NAME.conf"

echo "🔍 Loading environment variables from .env..."
export $(grep -v '^#' .env | xargs)

# Check which docker-compose command is available
echo "🔎 Checking Docker Compose installation..."
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_CMD="docker compose"
    echo "✅ Found: docker compose (Docker CLI plugin)"
elif command -v docker-compose &> /dev/null; then
    DOCKER_CMD="docker-compose"
    echo "✅ Found: docker-compose (legacy standalone)"
else
    echo "❌ Neither 'docker compose' nor 'docker-compose' is installed. Please install Docker Compose."
    exit 1
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

# Build or pull depending on environment
if [ -n "${SUBVORTEX_LOCAL:-}" ]; then
    echo "🔨 Local development detected (SUBVORTEX_LOCAL is set). Building validator-redis image..."
    $DOCKER_CMD -f ../docker-compose.local.yml build validator-redis
else
    echo "📥 Production mode detected. Pulling validator-redis image..."
    $DOCKER_CMD -f ../docker-compose.yml pull validator-redis
fi

echo "✅ Validator Redis Docker setup completed successfully."
