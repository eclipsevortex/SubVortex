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
    cd "$TARGET_DIR"
else
    echo "📁 Using fallback PROJECT_ROOT: $SCRIPT_DIR"
    cd "$SCRIPT_DIR"
fi

echo "📍 Working directory: $(pwd)"

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

# Build or pull depending on environment
if [ -n "${SUBVORTEX_LOCAL:-}" ]; then
    echo "🔨 Local development detected (SUBVORTEX_LOCAL is set). Building validator-redis image..."
    $DOCKER_CMD -f ../docker-compose.local.yml build validator-redis
else
    echo "📥 Production mode detected. Pulling validator-redis image..."
    $DOCKER_CMD -f ../docker-compose.yml pull validator-redis
fi

echo "✅ Validator Redis Docker setup completed successfully."
