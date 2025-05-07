#!/bin/bash

set -euo pipefail

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Load utility functions if available
source ../../scripts/utils.sh

# Help function
show_help() {
    echo "Usage: $0 [--create | --restore] --mode [rdb|aof|raw] --dump <path> [--index <db_index>]"
    echo
    echo "Options:"
    echo "  --create      Create a backup"
    echo "  --restore     Restore from a backup"
    echo "  --mode        Backup mode: 'rdb' or 'aof'"
    echo "  --dump        Path to the backup file or directory"
    echo "  --index       Redis database index (default: 0)"
    echo "  --help        Show this help message"
    exit 0
}

# Default values
CREATE=false
RESTORE=false
MODE=""
DUMP_PATH=""
DB_INDEX="0"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --create)
            CREATE=true
            shift
        ;;
        --restore)
            RESTORE=true
            shift
        ;;
        --mode)
            MODE="$2"
            shift 2
        ;;
        --dump)
            DUMP_PATH="$2"
            shift 2
        ;;
        --index)
            DB_INDEX="$2"
            shift 2
        ;;
        --help)
            show_help
        ;;
        *)
            echo "Unrecognized option '$1'"
            show_help
        ;;
    esac
done

# Validate required arguments
if [[ -z "$MODE" || -z "$DUMP_PATH" ]]; then
    echo "❌ Error: --mode and --dump are required."
    show_help
fi

REDIS_USER="redis"
REDIS_GROUP="redis"

# Function to determine Redis data directory
get_redis_data_dir() {
    redis-cli -n "$DB_INDEX" CONFIG GET dir | awk 'NR==2'
}

# Function to determine Redis password if required
get_redis_password() {
    if [[ -n "${REDIS_PASSWORD:-}" ]]; then
        echo "$REDIS_PASSWORD"
    else
        echo ""
    fi
}

# Function to create a Redis RDB dump
create_rdb_dump() {
    echo "🔄 Initiating Redis RDB dump creation..."
    
    REDISCLI_AUTH=$(get_redis_password)
    export REDISCLI_AUTH
    
    redis-cli -n "$DB_INDEX" SAVE > /dev/null
    
    REDIS_DIR=$(get_redis_data_dir)
    if [[ -z "$REDIS_DIR" ]]; then
        echo "❌ Unable to determine Redis data directory."
        exit 1
    fi
    
    if [[ ! -f "$REDIS_DIR/dump.rdb" ]]; then
        echo "❌ Redis dump file not found at $REDIS_DIR/dump.rdb"
        exit 1
    fi
    
    cp -f "$REDIS_DIR/dump.rdb" "$DUMP_PATH"
    echo "✅ Redis RDB dump successfully created at $DUMP_PATH"
}

# Function to restore Redis from an RDB dump
restore_rdb_dump() {
    echo "♻️ Initiating Redis RDB restoration from dump..."
    
    REDISCLI_AUTH=$(get_redis_password)
    export REDISCLI_AUTH
    
    if [[ ! -f "$DUMP_PATH" ]]; then
        echo "❌ Specified dump file not found at $DUMP_PATH"
        exit 1
    fi
    
    REDIS_DIR=$(get_redis_data_dir)
    if [[ -z "$REDIS_DIR" ]]; then
        echo "❌ Unable to determine Redis data directory."
        exit 1
    fi
    
    echo "🛑 Stopping Redis service..."
    sudo systemctl stop redis-server
    
    if [[ -f "$REDIS_DIR/dump.rdb" ]]; then
        TIMESTAMP=$(date +"%Y%m%d%H%M%S")
        sudo mv "$REDIS_DIR/dump.rdb" "$REDIS_DIR/dump.rdb.bak.$TIMESTAMP"
        echo "📦 Existing dump backed up as dump.rdb.bak.$TIMESTAMP"
    fi
    
    sudo cp -f "$DUMP_PATH" "$REDIS_DIR/dump.rdb"
    sudo chown "$REDIS_USER:$REDIS_GROUP" "$REDIS_DIR/dump.rdb"
    sudo chmod 660 "$REDIS_DIR/dump.rdb"
    echo "✅ New dump file placed at $REDIS_DIR/dump.rdb"
    
    echo "🚀 Starting Redis service..."
    sudo systemctl start redis-server
    
    echo "✅ Redis RDB restoration completed successfully."
}

# Function to create a Redis AOF dump
create_aof_dump() {
    echo "🔄 Initiating Redis AOF dump creation..."
    
    REDISCLI_AUTH=$(get_redis_password)
    export REDISCLI_AUTH
    
    redis-cli -n "$DB_INDEX" BGREWRITEAOF > /dev/null
    
    # Wait for BGREWRITEAOF to complete
    while true; do
        STATUS=$(redis-cli -n "$DB_INDEX" INFO persistence | grep aof_rewrite_in_progress | awk -F: '{print $2}' | tr -d '\r')
        if [[ "$STATUS" == "0" ]]; then
            break
        fi
        sleep 1
    done
    
    REDIS_DIR=$(get_redis_data_dir)
    if [[ -z "$REDIS_DIR" ]]; then
        echo "❌ Unable to determine Redis data directory."
        exit 1
    fi
    
    AOF_DIR="$REDIS_DIR/appendonlydir"
    if [[ ! -d "$AOF_DIR" ]]; then
        echo "❌ AOF directory not found at $AOF_DIR"
        exit 1
    fi
    
    if [[ -e "$DUMP_PATH" ]]; then
        rm -rf "$DUMP_PATH"
    fi
    
    cp -r "$AOF_DIR" "$DUMP_PATH"
    echo "✅ Redis AOF dump successfully created at $DUMP_PATH"
}

# Function to restore Redis from an AOF dump
restore_aof_dump() {
    echo "♻️ Initiating Redis AOF restoration from dump..."
    
    REDISCLI_AUTH=$(get_redis_password)
    export REDISCLI_AUTH
    
    if [[ ! -d "$DUMP_PATH" ]]; then
        echo "❌ Specified AOF dump directory not found at $DUMP_PATH"
        exit 1
    fi
    
    REDIS_DIR=$(get_redis_data_dir)
    if [[ -z "$REDIS_DIR" ]]; then
        echo "❌ Unable to determine Redis data directory."
        exit 1
    fi
    
    echo "🛑 Stopping Redis service..."
    sudo systemctl stop redis-server
    
    AOF_DIR="$REDIS_DIR/appendonlydir"
    if [[ -d "$AOF_DIR" ]]; then
        TIMESTAMP=$(date +"%Y%m%d%H%M%S")
        sudo mv "$AOF_DIR" "$REDIS_DIR/appendonlydir.bak.$TIMESTAMP"
        echo "📦 Existing AOF directory backed up as appendonlydir.bak.$TIMESTAMP"
    fi
    
    sudo cp -r "$DUMP_PATH" "$AOF_DIR"
    sudo chown -R "$REDIS_USER:$REDIS_GROUP" "$AOF_DIR"
    echo "✅ New AOF files placed at $AOF_DIR"
    
    echo "🚀 Starting Redis service..."
    sudo systemctl start redis-server
    
    echo "✅ Redis AOF restoration completed successfully."
}

# Function to create a raw dump (key-by-key) of a specific DB index
create_raw_dump() {
    echo "🔄 Creating base64-safe dump of Redis DB index $DB_INDEX..."

    # Coming soon

    echo "✅ Key-by-key base64 dump created at $DUMP_PATH"
}

# Function to restore a raw dump (key-by-key) into a specific DB index
restore_raw_dump() {
    echo "♻️ Restoring base64-safe dump into Redis DB index $DB_INDEX..."

    # Coming soon

    echo "✅ Base64-safe restore completed"
}

# Execute the requested operation
if [[ "$CREATE" == true ]]; then
    if [[ "$MODE" == "rdb" ]]; then
        create_rdb_dump
    elif [[ "$MODE" == "aof" ]]; then
        create_aof_dump
    # elif [[ "$MODE" == "raw" ]]; then
    #     create_raw_dump
    else
        echo "❌ Invalid mode specified. Use 'rdb' or 'aof'."
        exit 1
    fi
elif [[ "$RESTORE" == true ]]; then
    if [[ "$MODE" == "rdb" ]]; then
        restore_rdb_dump
    elif [[ "$MODE" == "aof" ]]; then
        restore_aof_dump
    # elif [[ "$MODE" == "raw" ]]; then
    #     restore_raw_dump
    else
        echo "❌ Invalid mode specified. Use 'rdb' or 'aof'."
        exit 1
    fi
else
    echo "❌ No operation specified. Use --create or --restore."
    show_help
fi
