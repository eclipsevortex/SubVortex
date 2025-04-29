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

uninstall_redis_ubuntu() {
    echo "Stopping and uninstalling Redis on Ubuntu..."
    sudo systemctl stop redis-server
    sudo systemctl disable redis-server
    sudo apt purge -y redis-server
    sudo apt autoremove -y
    sudo rm -rf /etc/redis /var/lib/redis /var/log/redis
    sudo systemctl daemon-reload
    sudo systemctl reset-failed

    echo "Redis uninstallation complete on Ubuntu."
}

uninstall_redis_macos() {
    echo "Stopping and uninstalling Redis on macOS..."
    if command -v brew &>/dev/null; then
        brew services stop redis
        brew uninstall redis
        echo "Redis uninstallation complete on macOS."
    else
        echo "Homebrew not found. Skipping Redis removal."
    fi
}

case "$os" in
    "linux")
        uninstall_redis_ubuntu
    ;;
    "macos")
        uninstall_redis_macos
    ;;
    *)
        echo "Unsupported operating system: $os"
        exit 1
    ;;
esac

echo "✅ Validator Redis teardown completed successfully."