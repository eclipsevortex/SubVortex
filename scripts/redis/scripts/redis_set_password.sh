#!/bin/bash

# This script protected redis with a password

show_help() {
cat << EOF
Usage: ${0##*/} [-c ARG] [-a ARG] [-s] [-h] -- Configure the password for redis

    -c | --config ARG       path of the redis.conf, default /etc/redis/redis.conf
    -a | --password ARG     password to protect redis instance
    -s | --silent           if provided, nothing will be redirected to the ouput, false otherwise
    -h | --help             display the help
EOF
}

OPTIONS="c:a:sh"
LONGOPTIONS="config:,password:,silent:,help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

REDIS_CONF=/etc/redis/redis.conf
REDIS_PASSWORD=$(openssl rand -base64 20)
SILENT=false

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

# Set the password
sed -i "s,^# requirepass foobared,requirepass $REDIS_PASSWORD," $REDIS_CONF
! $SILENT && echo -e "\\033[32mPassword configured\\033[0m"

# Notification
! $SILENT && echo -e "\\033[32mPassword setup\\033[0m"

# Restart redis
status=$(sudo systemctl is-active --quiet redis-server.service && echo 1 || echo 0)
if [[ $status == 1 ]]; then
    sudo systemctl restart redis-server.service
fi