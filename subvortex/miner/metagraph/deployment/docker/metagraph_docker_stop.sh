#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-miner-metagraph
SERVICE_KEY="miner-metagraph"
PROJECT_WORKING_DIR="${SUBVORTEX_WORKING_DIR:-}"

echo "🛑 Stopping $SERVICE_NAME..."

# Fallback to script location if PROJECT_WORKING_DIR is not set
if [[ -z "$PROJECT_WORKING_DIR" ]]; then
  SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PROJECT_WORKING_DIR="$(realpath "$SCRIPT_PATH/../../../../../")"
  echo "📁 PROJECT_WORKING_DIR not set — using fallback: $PROJECT_WORKING_DIR"
else
  echo "📁 Using PROJECT_WORKING_DIR from environment: $PROJECT_WORKING_DIR"
fi

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

# Choose compose file
echo "🔎 Detecting Docker Compose file..."
if [ -n "${SUBVORTEX_LOCAL:-}" ]; then
    echo "🛠 Local environment detected (SUBVORTEX_LOCAL is set). Using local compose file."
    COMPOSE_FILE="../docker-compose.local.yml"
else
    echo "🌍 Production environment detected. Using standard compose file."
    COMPOSE_FILE="../docker-compose.yml"
fi

# Stop the miner-neuron container
echo "🛑 Stopping container..."
$DOCKER_CMD -f "$COMPOSE_FILE" stop "$SERVICE_KEY"

echo "✅ $SERVICE_NAME stopped successfully."