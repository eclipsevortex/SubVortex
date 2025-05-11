#!/bin/bash

function install_npm() {
    # Check pm2 is already installed
    if command -v npm &> /dev/null; then
        return
    fi
    
    # Install npm
    sudo apt-get install -y nodejs npm
}

function install_pm2() {
    # Check pm2 is already installed
    if command -v pm2 &> /dev/null; then
        return
    fi
    
    # Install pre-requisites
    install_npm
    
    # Install pm2
    sudo npm i -g pm2
}

function install_redis_if_needed() {
    REQUIRED_VERSION="8.0.0"

    get_redis_version() {
        command -v redis-server >/dev/null && redis-server --version | awk '{print $3}' | cut -d'=' -f2
    }

    echo "📦 Checking Redis installation..."

    if [[ "$(get_redis_version)" == "$REQUIRED_VERSION" ]]; then
        echo "✅ Redis v$REQUIRED_VERSION is already installed."
        return
    fi

    echo "🔍 Redis is not installed or not at version $REQUIRED_VERSION. Proceeding with upgrade..."

    # Stop existing Redis service safely
    echo "🛑 Stopping existing Redis service (if running)..."
    sudo systemctl stop redis-server || true

    # Backup Redis data directory
    REDIS_CONF_PATH="${SUBVORTEX_REDIS_CONFIG:-/etc/redis/redis.conf}"
    REDIS_DATA_DIR=$(grep -E '^\s*dir\s+' "$REDIS_CONF_PATH" | awk '{print $2}')
    BACKUP_DIR="/var/tmp/redis-backup-$(date +%Y%m%d%H%M%S)"

    if [[ -n "$REDIS_DATA_DIR" && -d "$REDIS_DATA_DIR" ]]; then
        echo "💾 Backing up Redis data from $REDIS_DATA_DIR to $BACKUP_DIR"
        sudo cp -a "$REDIS_DATA_DIR" "$BACKUP_DIR"
    else
        echo "⚠️ Could not determine or access Redis data directory — skipping backup."
    fi

    # Remove existing Redis (if installed via APT)
    if dpkg -l | grep -q redis-server; then
        echo "🧹 Removing existing Redis installation from APT..."
        sudo apt-get remove -y redis-server
    fi

    # Install Redis from source
    TMP_DIR="/tmp/redis-install"
    mkdir -p "$TMP_DIR"
    pushd "$TMP_DIR" > /dev/null

    REDIS_URL="http://download.redis.io/releases/redis-${REQUIRED_VERSION}.tar.gz"
    echo "⬇️ Downloading Redis $REQUIRED_VERSION..."
    curl -fsSL "$REDIS_URL" -o redis.tar.gz
    tar xzf redis.tar.gz
    cd "redis-$REQUIRED_VERSION"

    echo "⚙️ Building Redis from source..."
    make -j"$(nproc)"
    sudo make install

    popd > /dev/null
    rm -rf "$TMP_DIR"

    echo "✅ Redis v$REQUIRED_VERSION installed successfully."
}