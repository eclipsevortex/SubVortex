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

install_redis_ubuntu() {
    if command -v redis-server >/dev/null 2>&1; then
        echo "Redis is already installed on Ubuntu."
    else
        echo "Installing Redis on Ubuntu..."
        sudo apt update
        sudo apt install -y redis-server
        sudo systemctl enable redis-server
    fi
    
    if [[ -n "$SUBVORTEX_REDIS_PASSWORD" ]]; then
        echo "Setting Redis password..."
        REDIS_CONF="/etc/redis/redis.conf"
        if grep -q "^requirepass" "$REDIS_CONF"; then
            sudo sed -i "s/^requirepass .*/requirepass $SUBVORTEX_REDIS_PASSWORD/" "$REDIS_CONF"
        else
            sudo sed -i "/^# requirepass/a requirepass $SUBVORTEX_REDIS_PASSWORD" "$REDIS_CONF"
        fi
        sudo systemctl restart redis-server
    fi
}

install_redis_macos() {
    if command -v redis-server >/dev/null 2>&1; then
        echo "Redis is already installed on macOS."
    else
        echo "Installing Redis on macOS..."
        if ! command -v brew &>/dev/null; then
            echo "Homebrew is not installed. Installing Homebrew first..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install redis
    fi
    
    if [[ -n "$SUBVORTEX_REDIS_PASSWORD" ]]; then
        echo "Setting Redis password..."
        REDIS_CONF="/opt/homebrew/etc/redis.conf"
        if grep -q "^requirepass" "$REDIS_CONF"; then
            sed -i '' "s/^requirepass .*/requirepass $SUBVORTEX_REDIS_PASSWORD/" "$REDIS_CONF"
        else
            sed -i '' "s/^# requirepass .*/requirepass $SUBVORTEX_REDIS_PASSWORD/" "$REDIS_CONF"
        fi
    fi
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
