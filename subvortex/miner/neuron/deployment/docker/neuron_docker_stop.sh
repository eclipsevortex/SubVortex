#!/bin/bash

set -euo pipefail

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

echo "🔍 Loading environment variables from .env..."
export $(grep -v '^#' .env | xargs)

# Check Docker Compose availability
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

# Choose compose file
if [ -n "${SUBVORTEX_LOCAL:-}" ]; then
    echo "🛠 Local environment detected (SUBVORTEX_LOCAL is set). Using local compose file."
    COMPOSE_FILE="../docker-compose.local.yml"
else
    echo "🌍 Production environment detected. Using standard compose file."
    COMPOSE_FILE="../docker-compose.yml"
fi

# Stop the miner-neuron container
echo "🛑 Stopping Miner Neuron container..."
$DOCKER_CMD -f "$COMPOSE_FILE" stop miner-neuron

echo "✅ Miner Neuron container stopped successfully."
