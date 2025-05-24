#!/bin/bash

# === ⚙️ Config ===
TMP_PORT=6380
TMP_REDIS_DIR=/tmp/redis_restore
TMP_REDIS_DUMP=$TMP_REDIS_DIR/dump.rdb
TMP_LOG=$TMP_REDIS_DIR/restore.log

LIVE_HOST=127.0.0.1
LIVE_PORT=6379
LIVE_PASS=""
TMP_PASS=""

SOURCE_DUMP_PATH=""  # Will be set from argument

# === 🛠️ Argument parsing ===
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --dump)
            SOURCE_DUMP_PATH="$2"
            shift 2
            ;;
        --live-pass)
            LIVE_PASS="$2"
            shift 2
            ;;
        --tmp-pass)
            TMP_PASS="$2"
            shift 2
            ;;
        *)
            echo "❌ Unknown parameter: $1"
            exit 1
            ;;
    esac
done

if [ ! -f "$SOURCE_DUMP_PATH" ]; then
    echo "❌ Provided dump not found: $SOURCE_DUMP_PATH"
    exit 1
fi

# === 🔐 Auth setup ===
LIVE_AUTH_CMD=""
TMP_AUTH_CMD=""
if [ -n "$LIVE_PASS" ]; then
    LIVE_AUTH_CMD="-a $LIVE_PASS"
fi
if [ -n "$TMP_PASS" ]; then
    TMP_AUTH_CMD="-a $TMP_PASS"
fi

# === 🚀 Launch temporary Redis ===
echo "📦 Starting temporary Redis on port $TMP_PORT..."
mkdir -p "$TMP_REDIS_DIR"
cp "$SOURCE_DUMP_PATH" "$TMP_REDIS_DUMP"

redis-server --port $TMP_PORT --dir $TMP_REDIS_DIR --daemonize yes --logfile "$TMP_LOG"

# === 🕒 Wait until temp Redis is ready ===
echo "⏳ Waiting for temp Redis to become available..."
until redis-cli -p $TMP_PORT $TMP_AUTH_CMD PING | grep -q "PONG"; do
    sleep 1
done
echo "✅ Temp Redis is up on port $TMP_PORT"

# === 🔁 Sync keys from temp Redis to live Redis ===
echo "🔄 Starting restore from dump to live Redis..."
cursor=0
total=0

while : ; do
    RESP=$(redis-cli -p $TMP_PORT $TMP_AUTH_CMD SCAN $cursor COUNT 100)
    cursor=$(echo "$RESP" | head -1)
    keys=$(echo "$RESP" | tail -n +2)

    for key in $keys; do
        ttl=$(redis-cli -p $TMP_PORT $TMP_AUTH_CMD PTTL "$key")
        [[ $ttl -lt 0 ]] && ttl=0
        data=$(redis-cli -p $TMP_PORT $TMP_AUTH_CMD DUMP "$key")
        if [ -n "$data" ]; then
            redis-cli -h $LIVE_HOST -p $LIVE_PORT $LIVE_AUTH_CMD RESTORE "$key" $ttl "$data" REPLACE > /dev/null 2>&1
            ((total++))
        fi
    done

    [[ "$cursor" == "0" ]] && break
done

echo "🎉 Restored $total keys to live Redis!"

# === 🧹 Cleanup ===
echo "🧼 Shutting down temp Redis and cleaning up..."
redis-cli -p $TMP_PORT $TMP_AUTH_CMD SHUTDOWN NOSAVE > /dev/null 2>&1
rm -rf "$TMP_REDIS_DIR"

echo "✅ Restore complete with zero downtime!"
