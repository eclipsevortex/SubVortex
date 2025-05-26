#!/bin/sh

# Create Redis working directory if specified in redis.conf
REDIS_DATA_DIR=$(grep -E '^\s*dir\s+' "/etc/redis/redis.conf" | awk '{print $2}')
if [[ -n "$REDIS_DATA_DIR" ]]; then
    echo "📁 Ensuring Redis data directory exists: $REDIS_DATA_DIR"
    sudo mkdir -p "$REDIS_DATA_DIR"
    sudo chown root:root "$REDIS_DATA_DIR"
else
    echo "⚠️ Could not determine Redis data directory from redis.conf."
fi

# Start Redis with the password provided via REDIS_PASSWORD environment variable
exec redis-server --requirepass "$SUBVORTEX_REDIS_PASSWORD"