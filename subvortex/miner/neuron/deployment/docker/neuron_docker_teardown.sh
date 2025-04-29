#!/bin/bash

set -e

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Check which command is available
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_CMD="docker-compose"
else
    echo "❌ Neither 'docker compose' nor 'docker-compose' is installed. Please install Docker Compose."
    exit 1
fi

if [ -n "$SUBVORTEX_LOCAL" ]; then
    $DOCKER_CMD -f ../docker-compose.local.yml down miner-neuron --rmi all
else
    $DOCKER_CMD -f ../docker-compose.yml down miner-neuron --rmi all
fi

echo "✅ Miner Neuron teardown completed successfully."
