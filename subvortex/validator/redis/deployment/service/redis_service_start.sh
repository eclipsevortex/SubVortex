#!/bin/bash

set -e

# Include files
source ${BASH_SOURCE%/*}/../../../../../scripts/utils/machine.sh

# Get the OS
os=$(get_os)

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Load environment variables
export $(grep -v '^#' .env | xargs)

case "$os" in
    "linux")
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            if [[ "$ID" == "ubuntu" ]]; then
                if systemctl is-active --quiet redis-server; then
                    echo "Redis is already running on Ubuntu."
                else
                    echo "Starting Redis on Ubuntu..."
                    sudo systemctl start redis-server
                fi
            else
                echo "Unsupported Linux distribution. Please install Redis manually."
                exit 1
            fi
        fi
        ;;
    "macos")
        if pgrep redis-server >/dev/null; then
            echo "Redis is already running on macOS."
        else
            echo "Starting Redis on macOS..."
            brew services start redis
        fi
        ;;
    *)
        echo "Unsupported operating system: $OS"
        exit 1
        ;;
esac

echo "✅ Validator Redis started successfully"
