#!/bin/bash

set -e

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Check which command is available
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_CMD="docker compose"
    elif command -v docker-compose &> /dev/null; then
    DOCKER_CMD="docker-compose"
else
    echo "Neither 'docker compose' nor 'docker-compose' is installed. Please install Docker Compose."
    exit 1
fi

# Choose appropriate compose file
if [ -n "$SUBVORTEX_LOCAL" ]; then
    COMPOSE_FILE="../docker-compose.local.yml"
else
    COMPOSE_FILE="../docker-compose.yml"
fi

# Check if validator-redis container is running
IS_RUNNING=$($DOCKER_CMD -f "$COMPOSE_FILE" ps -q validator-redis | xargs docker inspect -f '{{.State.Running}}' 2>/dev/null || echo "false")

# Build and run command
if [ "$IS_RUNNING" != "true" ]; then
    echo "🔄 Container not running — forcing recreate..."
    $DOCKER_CMD -f "$COMPOSE_FILE" up validator-redis -d --no-deps --force-recreate
else
    echo "⚙️  Container already running — starting without recreate..."
    $DOCKER_CMD -f "$COMPOSE_FILE" up validator-redis -d --no-deps
fi

echo "✅ Validator Redis started successfully"
