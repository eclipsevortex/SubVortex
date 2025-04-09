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

install_redis_ubuntu() {
    echo "Installing Redis on Ubuntu..."
    sudo apt update
    sudo apt install -y redis-server
    sudo systemctl enable redis-server

    if [[ -n "$REDIS_PASSWORD" ]]; then
        echo "Setting Redis password..."
        sudo sed -i "/^# requirepass/c\requirepass $REDIS_PASSWORD" /etc/redis/redis.conf
        sudo systemctl restart redis-server
    fi
}

install_redis_macos() {
    echo "Installing Redis on macOS..."
    if ! command -v brew &>/dev/null; then
        echo "Homebrew is not installed. Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    brew install redis

    # Add a password
    sed -i '' "s/^# requirepass .*/requirepass $REDIS_PASSWORD/" /opt/homebrew/etc/redis.conf
}

case "$os" in
    "linux")
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            if [[ "$ID" == "ubuntu" ]]; then
                install_redis_ubuntu
            else
                echo "Unsupported Linux distribution. Please install Redis manually."
                exit 1
            fi
        fi
        ;;
    "macos")
        install_redis_macos
        ;;
    *)
        echo "Unsupported operating system: $OS"
        exit 1
        ;;
esac

echo "✅ Validator Redis setup successfully"
