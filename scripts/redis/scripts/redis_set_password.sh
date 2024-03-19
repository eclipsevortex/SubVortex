#!/bin/bash

# This script protected redis with a password

show_help() {
cat << EOF
Usage: ${0##*/} [-c ARG] [-a ARG] [-h] -- Configure the password for redis

    -c | --config ARG       path of the redis.conf, default /etc/redis/redis.conf
    -a | --password ARG     password to protect redis instance
    -h | --help             display the help
EOF
}

OPTIONS="c:a:h"
LONGOPTIONS="config:,password:,help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

REDIS_CONF=/etc/redis/redis.conf
REDIS_PASSWORD=$(openssl rand -base64 20)

while [ "$#" -gt 0 ]; do
    case "$1" in
        -c | --config)
            REDIS_CONF="$2"
            shift 2
        ;;
        -a | --password)
            REDIS_PASSWORD="$2"
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

# Set the password
sed -i "s,^# requirepass foobared,requirepass $REDIS_PASSWORD," $REDIS_CONF
echo -e "\\033[32mPassword configured\\033[0m"

# Notification
echo -e "\\033[32mPassword setup\\033[0m"

# Restart redis
systemctl restart redis-server.service
