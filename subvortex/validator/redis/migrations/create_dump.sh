#!/bin/bash

# === 🧰 Configuration ===
REDIS_CLI=/usr/bin/redis-cli
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DUMP_PATH=/var/lib/redis/dump.rdb
BACKUP_DIR=/var/backups/redis
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="redis_backup_$TIMESTAMP.rdb"
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

# === 🧪 Test Redis connection ===
echo "🔍 Checking Redis connection..."
if ! $REDIS_CLI -h $REDIS_HOST -p $REDIS_PORT $AUTH_CMD PING | grep -q "PONG"; then
    echo "❌ Redis connection failed. Please check host, port, or password."
    exit 1
fi

# === 📦 Trigger BGSAVE ===
echo "📤 Triggering Redis BGSAVE..."
$REDIS_CLI -h $REDIS_HOST -p $REDIS_PORT $AUTH_CMD BGSAVE

# === ⏳ Wait for BGSAVE to complete ===
echo "🕒 Waiting for BGSAVE to complete..."
while true; do
    LAST_SAVE=$($REDIS_CLI -h $REDIS_HOST -p $REDIS_PORT $AUTH_CMD LASTSAVE)
    NOW=$(date +%s)
    if [ $((NOW - LAST_SAVE)) -lt 5 ]; then
        echo "✅ BGSAVE completed at $(date -d @$LAST_SAVE)"
        break
    fi
    sleep 1
done

# === 🗃️ Backup directory setup ===
mkdir -p "$BACKUP_DIR"

# === 📂 Copy dump.rdb to backup location ===
echo "📁 Copying dump to $BACKUP_DIR/$BACKUP_NAME"
cp "$REDIS_DUMP_PATH" "$BACKUP_DIR/$BACKUP_NAME"

echo "🎉 Redis backup complete: $BACKUP_DIR/$BACKUP_NAME"
