#!/bin/bash

set -e

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Include files
source ../../../scripts/utils/machine.sh

# Get the OS
os=$(get_os)

# Load environment variables
export $(grep -v '^#' .env | xargs)

start_linux_redis() {
    systemctl daemon-reexec
    systemctl daemon-reload
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "Redis is already started on Ubuntu."
    else
        systemctl start redis-server
    fi
}

start_macos_redis() {
    if pgrep redis-server >/dev/null; then
        brew services restart redis
    else
        brew services start redis
    fi
}

case "$os" in
    "linux")
        start_linux_redis
    ;;
    "macos")
        start_macos_redis
    ;;
    *)
        echo "Unsupported operating system: $OS"
        exit 1
    ;;
esac

echo "✅ Validator Redis started successfully"
