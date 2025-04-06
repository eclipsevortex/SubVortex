#!/bin/bash

set -e

# Include files
source ${BASH_SOURCE%/*}/../../../../../scripts/utils/machine.sh

# Get the OS
os=$(get_os)

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

uninstall_redis_ubuntu() {
    echo "Stopping and uninstalling Redis on Ubuntu..."
    sudo systemctl stop redis-server
    sudo systemctl disable redis-server
    sudo apt remove -y redis-server
    sudo apt autoremove -y
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
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            if [[ "$ID" == "ubuntu" ]]; then
                uninstall_redis_ubuntu
            else
                echo "Unsupported Linux distribution. Please uninstall Redis manually."
                exit 1
            fi
        fi
    ;;
    "macos")
        uninstall_redis_macos
    ;;
    *)
        echo "Unsupported operating system: $os"
        exit 1
    ;;
esac

echo "✅ Validator teardown completed successfully."