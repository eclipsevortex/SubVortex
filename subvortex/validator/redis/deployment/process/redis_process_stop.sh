#!/bin/bash

set -e

# Determine script directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Include files
source ../../../scripts/utils/machine.sh

# Get the OS
os=$(get_os)

# Load environment variables
export $(grep -v '^#' .env | xargs)

stop_linux_redis() {
    if systemctl is-active --quiet redis-server; then
        echo "🛑 Stopping Redis on Ubuntu..."
        sudo systemctl stop redis-server
    else
        echo "ℹ️ Redis is not running on Ubuntu."
    fi
}

stop_macos_redis() {
    if pgrep redis-server >/dev/null; then
        echo "🛑 Stopping Redis on macOS..."
        brew services stop redis
    else
        echo "ℹ️ Redis is not running on macOS."
    fi
}

case "$os" in
    "linux")
        stop_linux_redis
    ;;
    "macos")
        stop_macos_redis
    ;;
    *)
        echo "Unsupported operating system: $os"
        exit 1
    ;;
esac

echo "✅ Redis stopped successfully"
