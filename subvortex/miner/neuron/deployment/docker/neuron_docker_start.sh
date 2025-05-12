#!/bin/bash

set -euo pipefail

# Determine working directory: prefer SUBVORTEX_WORKING_DIR, fallback to script location
SCRIPT_DIR="$(cd "$(dirname "$(python3 -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$0")")" && pwd)"

# Find project root by walking up until LICENSE is found
find_project_root() {
    local dir="$1"
    while [[ "$dir" != "/" ]]; do
        [[ -f "$dir/LICENSE" ]] && { echo "$dir"; return; }
        dir="$(dirname "$dir")"
    done
    return 1
}

PROJECT_ROOT="$(find_project_root "$SCRIPT_DIR")" || {
    echo "❌ Could not detect project root (LICENSE not found)"
    exit 1
}

# Resolve final working directory
if [[ -n "${SUBVORTEX_WORKING_DIR:-}" ]]; then
    REL_PATH="${SCRIPT_DIR#$PROJECT_ROOT/}"
    TARGET_DIR="$SUBVORTEX_WORKING_DIR/$REL_PATH"
    [[ -d "$TARGET_DIR" ]] || { echo "❌ Target directory does not exist: $TARGET_DIR"; exit 1; }
    echo "📁 Using SUBVORTEX_WORKING_DIR: $TARGET_DIR"
    cd "$TARGET_DIR/../.."
else
    echo "📁 Using fallback PROJECT_ROOT: $SCRIPT_DIR"
    cd "$SCRIPT_DIR/../.."
fi

echo "📍 Working directory: $(pwd)"

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

# Load environment variables
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

# Build the docker-compose command
echo "🚀 Preparing to start Miner Neuron container..."
CMD="$DOCKER_CMD -f \"$COMPOSE_FILE\" up miner-neuron -d --no-deps"
if [[ "$RECREATE" == "true" || "$RECREATE" == "True" ]]; then
    echo "♻️ Recreate requested — will force recreate the container."
    CMD+=" --force-recreate"
fi

# Execute
echo "⚡ Executing: $CMD"
eval "$CMD"

echo "✅ Miner Neuron container started successfully."