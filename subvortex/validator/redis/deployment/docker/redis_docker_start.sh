#!/bin/bash

set -e

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

show_help() {
    echo "Usage: $0 [--recreate]"
    echo
    echo "Description:"
    echo "  This script start the validator redis"
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

# Clean the workspace with --remove if requested
CMD="$DOCKER_CMD -f "$COMPOSE_FILE" up validator-redis -d --no-deps"
if [[ "$RECREATE" == "true" || "$RECREATE" == "True" ]]; then
    CMD+=" --force-recreate"
fi

# Execute the command
eval "$CMD"

echo "✅ Validator Redis started successfully"
