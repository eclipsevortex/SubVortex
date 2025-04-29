#!/bin/bash

set -euo pipefail

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

echo "📦 Starting Validator Neuron Docker setup..."

# Load environment variables
echo "🔍 Loading environment variables from .env..."
export $(grep -v '^#' .env | xargs)

# Detect Docker Compose command
echo "🔎 Detecting Docker Compose command..."
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_CMD="docker compose"
    echo "✅ Using 'docker compose'."
elif command -v docker-compose &> /dev/null; then
    DOCKER_CMD="docker-compose"
    echo "✅ Using 'docker-compose'."
else
    echo "❌ Neither 'docker compose' nor 'docker-compose' is installed. Please install Docker Compose."
    exit 1
fi

# Choose compose file depending on environment
if [ -n "${SUBVORTEX_LOCAL:-}" ]; then
    echo "🛠️ Local mode detected — building validator-neuron service from source..."
    $DOCKER_CMD -f ../docker-compose.local.yml build validator-neuron
else
    echo "🌐 Pulling validator-neuron image from remote registry..."
    $DOCKER_CMD -f ../docker-compose.yml pull validator-neuron
fi

echo "✅ Validator Neuron Docker setup completed successfully."
