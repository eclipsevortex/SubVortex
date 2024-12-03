#!/bin/bash

# This script install a redis instance as process on your base environment

show_help() {
cat << EOF
Usage: ${0##*/} [-c ARG] [-p ARG] [-a ARG] [-h] -- Install redis as process in your base environment

    -c | --config ARG       path of the redis.conf, default /etc/redis/redis.conf
    -p | --port ARG         port of the redis instance, default 6379
    -a | --password ARG     password to protect redis instance
    -h | --help             display the help
EOF
}

OPTIONS="c:p:i:a:d:h"
LONGOPTIONS="config:,port:,install:,password:,data:,help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

REDIS_CONF=/etc/redis/redis.conf
REDIS_PORT=6379
REDIS_PASSWORD=$(openssl rand -base64 20)

while [ "$#" -gt 0 ]; do
    case "$1" in
        -c | --config)
            REDIS_CONF="$2"
            shift 2
        ;;
        -p | --port)
            REDIS_PORT="$2"
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

# Get the base path
current_dir=$(pwd)
relative_dir="SubVortex/scripts/redis"
if [[ $current_dir != *"SubVortex"* ]]; then
    BASE="${current_dir%/}/${relative_dir%/}"
else
    BASE="${current_dir%/}/${relative_dir#*/}"
fi

# Update package list
sudo apt-get update

# Install necessary packages
sudo apt install -y lsb-release curl gpg

# Download and store Redis GPG key in binary format
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg

# Add Redis repository to sources list with signed-by option
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list

# Install Redis server package with automatic "yes" response to prompts
sudo apt-get install -y redis

# Set the password
$BASE/scripts/redis_set_password.sh -c $REDIS_CONF -a $REDIS_PASSWORD 

# Disable rdb
$BASE/scripts/redis_disable_rdb.sh -c $REDIS_CONF

# Configure firewall
$BASE/scripts/redis_set_firewall.sh -p $REDIS_PORT