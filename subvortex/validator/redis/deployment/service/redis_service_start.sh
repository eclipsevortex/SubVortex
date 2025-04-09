#!/bin/bash

set -e

# Include files
source ${BASH_SOURCE%/*}/../../../../scripts/utils/machine.sh

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
                sudo systemctl start redis-server
            else
                echo "Unsupported Linux distribution. Please install Redis manually."
                exit 1
            fi
        fi
    ;;
    "macos")
        brew services start redis
    ;;
    *)
        echo "Unsupported operating system: $OS"
        exit 1
    ;;
esac

echo "✅ Validator Redis started successfully"
