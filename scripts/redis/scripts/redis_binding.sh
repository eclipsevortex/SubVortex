#!/bin/bash

# This script disable snapshots and enable AOF

show_help() {
cat << EOF
Usage: ${0##*/} [-c ARG] [-s] [-h] -- Change binding for redis

    -c | --config ARG       path of the redis.conf, default /etc/redis/redis.conf
    -s | --silent           if provided, nothing will be redirected to the ouput, false otherwise
    -h | --help             display the help
EOF
}

OPTIONS="c:sh"
LONGOPTIONS="config:,silent:,help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

REDIS_CONF=/etc/redis/redis.conf
SILENT=false

while [ "$#" -gt 0 ]; do
    case "$1" in
        -c | --config)
            REDIS_CONF="$2"
            shift 2
        ;;
        -s | --silent)
            SILENT=true
            shift 1
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

# Change binding
sudo sed -i 's/^bind 127.0.0.1 -::1/bind 0.0.0.0/' $REDIS_CONF

# Notification
! $SILENT && echo -e "\\033[32mBinding changed.\\033[0m"

# Restart redis
status=$(sudo systemctl is-active --quiet redis-server.service && echo 1 || echo 0)
if [[ $status == 1 ]]; then
    sudo systemctl restart redis-server.service
fi
