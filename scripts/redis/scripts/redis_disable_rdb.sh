#!/bin/bash

# This script disable snapshots and enable AOF

show_help() {
cat << EOF
Usage: ${0##*/} [-c ARG] [-h] -- Disable snapshots and enable AOF for redis

    -c | --config ARG       path of the redis.conf, default /etc/redis/redis.conf
    -h | --help             display the help
EOF
}

OPTIONS="c:h"
LONGOPTIONS="config:,help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

REDIS_CONF=/etc/redis/redis.conf

while [ "$#" -gt 0 ]; do
    case "$1" in
        -c | --config)
            REDIS_CONF="$2"
            shift 2
        ;;
        -h | --help)
            show_help
            exit 0
        ;;
        *)
            echo "Unrecognized option '$1'"
            exit 1
        ;;
    esac
done

# Create a backup
sudo cp $REDIS_CONF "${REDIS_CONF}.bak"

# Disable snapshots
sudo sed -i '/^save /d' $REDIS_CONF

# Enable AOF persistence
sudo sed -i 's/^appendonly no/appendonly yes/' $REDIS_CONF

# Notification
echo -e "\\033[32mRDB snapshots disabled, AOF persistence remains enabled.\\033[0m"

# Restart redis
sudo systemctl restart redis-server.service