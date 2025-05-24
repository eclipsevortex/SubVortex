#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-miner-neuron
SERVICE_KEY="miner-neuron"
PROJECT_WORKING_DIR="${SUBVORTEX_WORKING_DIR:-}"

echo "🚀 Starting $SERVICE_NAME..."

# Fallback to script location if PROJECT_WORKING_DIR is not set
if [[ -z "$PROJECT_WORKING_DIR" ]]; then
  SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PROJECT_WORKING_DIR="$(realpath "$SCRIPT_PATH/../../../../../")"
  echo "📁 PROJECT_WORKING_DIR not set — using fallback: $PROJECT_WORKING_DIR"
else
  echo "📁 Using PROJECT_WORKING_DIR from environment: $PROJECT_WORKING_DIR"
fi

PROJECT_EXECUTION_DIR="${SUBVORTEX_EXECUTION_DIR:-$PROJECT_WORKING_DIR}"
NEURON_WORKING_DIR="$PROJECT_WORKING_DIR/subvortex/miner"

show_help() {
    echo "Usage: $0 [--recreate]"
    echo
    echo "Description:"
    echo "  This script start the miner neuron"
    echo
    echo "Options:"
    echo "  --recreate    True if you want to recreate the container, false otherwise. Used when .env or volume have changed"
    echo "  --help        Show this help message"
    exit 0
}

OPTIONS="rh"
LONGOPTIONS="recreate,help"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"
if [ $? -ne 0 ]; then
    exit 1
fi

# Set defaults from env (can be overridden by arguments)
RECREATE=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
    case "$1" in
        -r|--recreate)
            RECREATE=true
            shift
        ;;
        -h | --help)
            show_help
            exit 0
        ;;
        *)
            echo "Unrecognized option '$1'"
            exit 1
        ;;
    esac
done

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
    COMPOSE_FILE="$NEURON_WORKING_DIR/docker-compose.local.yml"
else
    echo "🌍 Production environment detected. Using standard compose file."
    COMPOSE_FILE="$NEURON_WORKING_DIR/docker-compose.yml"
fi

# Build the docker-compose command
echo "🚀 Preparing to start container..."
CMD="$DOCKER_CMD -f \"$COMPOSE_FILE\" up \"$SERVICE_KEY\" -d --no-deps"
if [[ "$RECREATE" == "true" || "$RECREATE" == "True" ]]; then
    echo "♻️ Recreate requested — will force recreate the container."
    CMD+=" --force-recreate"
fi

# Execute
echo "⚡ Executing: $CMD"
eval "$CMD"

echo "✅ $SERVICE_NAME started successfully."