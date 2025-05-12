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
    
    # Backup Redis data directory if config is present
    REDIS_CONF_PATH="${SUBVORTEX_REDIS_CONFIG:-/etc/redis/redis.conf}"
    if [[ -f "$REDIS_CONF_PATH" ]]; then
        REDIS_DATA_DIR=$(grep -E '^\s*dir\s+' "$REDIS_CONF_PATH" | awk '{print $2}')
        BACKUP_DIR="/var/tmp/redis-backup-$(date +%Y%m%d%H%M%S)"
        
        if [[ -n "$REDIS_DATA_DIR" && -d "$REDIS_DATA_DIR" ]]; then
            echo "💾 Backing up Redis data from $REDIS_DATA_DIR to $BACKUP_DIR"
            sudo cp -a "$REDIS_DATA_DIR" "$BACKUP_DIR"
        else
            echo "⚠️ Could not determine or access Redis data directory — skipping backup."
        fi
    else
        echo "⚠️ Redis config file not found at $REDIS_CONF_PATH — skipping backup."
    fi
    
    # Remove existing Redis (if installed via APT)
    if dpkg -l | grep -q redis-server; then
        echo "🧹 Removing existing Redis installation from APT..."
        sudo apt-get remove -y redis-server
    fi
    
    # Build and install Redis
    TMP_DIR="/tmp/redis-install"
    REDIS_URL="http://download.redis.io/releases/redis-${REQUIRED_VERSION}.tar.gz"
    
    echo "⬇️ Downloading Redis $REQUIRED_VERSION..."
    mkdir -p "$TMP_DIR"
    curl -fsSL "$REDIS_URL" -o "$TMP_DIR/redis.tar.gz"
    
    tar -xzf "$TMP_DIR/redis.tar.gz" -C "$TMP_DIR"
    pushd "$TMP_DIR/redis-$REQUIRED_VERSION" > /dev/null
    
    echo "⚙️ Building Redis..."
    make -j"$(nproc)"
    
    echo "📥 Installing all Redis binaries..."
    cd src
    sudo make install
    
    # Copy redis.conf if not already installed
    if [[ ! -f /etc/redis/redis.conf ]]; then
        echo "📋 Installing redis.conf..."
        sudo mkdir -p /etc/redis
        sudo cp redis.conf /etc/redis/redis.conf
    fi
    
    popd > /dev/null
    rm -rf "$TMP_DIR"
    
    echo "✅ Redis v$REQUIRED_VERSION installed successfully."
}

# Desired Redis version
REQUIRED_REDIS_VERSION="6:8.0.0-1rl1~jammy1"

# Function to install specific version of redis-server if not already installed
install_specific_redis() {
    echo "📦 Checking installed Redis version..."
    current_version=$(dpkg-query -W -f='${Version}' redis-server 2>/dev/null || echo "none")
    
    if [[ "$current_version" == "$REQUIRED_REDIS_VERSION" ]]; then
        echo "✅ Redis version $REQUIRED_REDIS_VERSION is already installed."
        return
    fi
    
    echo "🔧 Installing Redis version $REQUIRED_REDIS_VERSION via apt-get..."
    
    # Ensure Redis is removed if a different version is installed
    if [[ "$current_version" != "none" ]]; then
        echo "🧹 Removing previously installed Redis version: $current_version"
        apt-get remove -y redis-server
    fi
    
    apt-get update

    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "redis-server=$REQUIRED_REDIS_VERSION" \
    -o Dpkg::Options::="--force-confdef" \
    -o Dpkg::Options::="--force-confnew"
}