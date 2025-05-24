#!/bin/bash

# === 🧰 Configuration ===
REDIS_CLI=/usr/bin/redis-cli
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DUMP_PATH=/var/lib/redis/dump.rdb
REDIS_PASSWORD=""

# === 🛠️ Argument parsing ===
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --pass)
            REDIS_PASSWORD="$2"
            shift 2
            ;;
        *)
            echo "❌ Unknown parameter: $1"
            exit 1
            ;;
    esac
done

# === 🔐 Auth command setup ===
AUTH_CMD=""
if [ -n "$REDIS_PASSWORD" ]; then
    AUTH_CMD="-a $REDIS_PASSWORD"
fi

# === 🔍 Check Redis is running ===
echo "🔍 Verifying Redis is reachable..."
if ! $REDIS_CLI -h $REDIS_HOST -p $REDIS_PORT $AUTH_CMD PING | grep -q "PONG"; then
    echo "❌ Redis connection failed. Please check host, port, or password."
    exit 1
fi

# === 🔎 Check for dump file ===
if [ -f "$REDIS_DUMP_PATH" ]; then
    echo "🗃️ Found dump file at: $REDIS_DUMP_PATH"
    echo "🗑️ Deleting dump.rdb..."
    rm -f "$REDIS_DUMP_PATH"
    echo "✅ dump.rdb successfully removed!"
else
    echo "ℹ️ No dump.rdb found at: $REDIS_DUMP_PATH"
fi
