#!/bin/bash
set -euo pipefail

# Help function
show_help() {
    echo "Usage: $0 [--version <version>]"
    echo
    echo "Description:"
    echo "  This script install redis"
    echo
    echo "Options:"
    echo "  --version   Redis version to install"
    echo "  --help      Show this help message"
    exit 0
}

OPTIONS="v:h"
LONGOPTIONS="version:,help:"

REDIS_VERSION="6:8.0.0-1rl1"

# Parse arguments
while [ "$#" -gt 0 ]; do
    case "$1" in
        -v |--version)
            REDIS_VERSION="$2"
            shift 2
        ;;
        -h | --help)
            show_help
            exit 0
        ;;
        --)
            shift
            break
            ;;
        *)
            echo "Unrecognized option '$1'"
            exit 1
        ;;
    esac
done

# Detect Ubuntu codename
UBUNTU_CODENAME=$(lsb_release -cs)

# Strip any suffix from user-provided version
if [[ "$REDIS_VERSION" == *"~"* ]]; then
    REDIS_VERSION="${REDIS_VERSION%%~*}"
fi

REDIS_VERSION="${REDIS_VERSION}~${UBUNTU_CODENAME}1"

echo "📦 Installing redis-server${REDIS_VERSION:+ (version $REDIS_VERSION)}..."

echo "🔐 Setting up Redis official APT repository for latest version..."

REDIS_LIST="/etc/apt/sources.list.d/redis.list"
REDIS_KEYRING="/usr/share/keyrings/redis-archive-keyring.gpg"

# Add keyring if missing
if [[ ! -f "$REDIS_KEYRING" ]]; then
  echo "🔑 Adding Redis GPG key..."
  curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o "$REDIS_KEYRING"
fi

# Add source list if missing
if [[ ! -f "$REDIS_LIST" ]]; then
  echo "📄 Adding Redis APT source..."
  echo "deb [signed-by=$REDIS_KEYRING] https://packages.redis.io/deb $(lsb_release -cs) main" | \
    sudo tee "$REDIS_LIST" > /dev/null
fi

echo "🔄 Updating APT..."

# Update Package Manager
sudo apt-get update

# Install specific or latest version
if [[ -n "$REDIS_VERSION" ]]; then
  echo "📥 Installing redis version: $REDIS_VERSION"
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    -o Dpkg::Options::="--force-confnew" \
    "redis=$REDIS_VERSION" \
    "redis-server=$REDIS_VERSION" \
    "redis-tools=$REDIS_VERSION"
else
  echo "📥 Installing latest available redis..."
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    -o Dpkg::Options::="--force-confnew" redis redis-server redis-tools
fi

echo "🔧 Unmasking redis-server service (if previously masked)..."
sudo systemctl stop redis-server.service || true
sudo systemctl disable redis-server.service || true
sudo systemctl mask redis-server.service || true

echo "✅ redis-server installation complete."