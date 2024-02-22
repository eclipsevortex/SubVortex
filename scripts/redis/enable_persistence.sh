#!/bin/bash

# Function to test for specific 'save' configurations
check_save_config() {
    local file=$1
    local expected=("$@")
    local found_all=true

    # Skip the first argument (file path)
    for i in "${expected[@]:1}"; do
        if ! sudo grep -q "^$i" "$file"; then
            echo "FAIL: Configuration 'save' does not contain '$i'"
            found_all=false
        fi
    done

    if [ "$found_all" = false ]; then
        return 1
    else
        echo "PASS: All 'save' configurations are correctly set."
        return 0
    fi
}

REDIS_CONF="/etc/redis/redis.conf"

if [ "$1" != "" ]; then
    REDIS_CONF="$1"
fi

# Backup original configuration file
sudo cp $REDIS_CONF "${REDIS_CONF}.bak"

# Check current 'save' configuration
check_save_config "$REDIS_CONF" "save 900 1" "save 300 10" "save 60 10000"
config_needs_update=$?

# Update configuration only if needed
if [ $config_needs_update -ne 0 ]; then
    # Enable AOF persistence
    sudo sed -i 's/^appendonly no/appendonly yes/' $REDIS_CONF
    sudo sed -i 's/^# appendfsync everysec/appendfsync everysec/' $REDIS_CONF

    # Update 'save' configuration
    sudo sed -i '/^save /d' $REDIS_CONF # Remove existing save lines
    echo -e "save 900 1\nsave 300 10\nsave 60 10000" | sudo tee -a $REDIS_CONF

    echo "Redis persistence configuration updated."

    # Restart Redis server
    sudo systemctl restart redis-server
    echo "Redis restarted."
else
    echo "No update needed for Redis persistence configuration."
fi

sudo systemctl status redis-server
