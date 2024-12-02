#!/bin/bash

# This script install a redis instance as docker container

show_help() {
cat << EOF
Usage: ${0##*/} [-c ARG] [-p ARG] [-a ARG] [-d ARG] [-s] [-h] -- Install redis as docker container

    -c | --config ARG       path of the redis.conf, default redis.conf
    -p | --port ARG         port of the redis instance, default 6379
    -a | --password ARG     password to protect redis instance
    -d | --data ARG         directory to store redis data, default /var/lib/redis
    -s | --silent           if provided, nothing will be redirected to the ouput, false otherwise
    -h | --help             display the help
EOF
}

OPTIONS="c:p:i:a:d:sh"
LONGOPTIONS="config:,port:,install:,password:,data:,silent:,help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

# Get the base path
current_dir=$(pwd)
relative_dir="SubVortex/scripts/redis"
if [[ $current_dir != *"SubVortex"* ]]; then
    BASE="${current_dir%/}/${relative_dir%/}"
else
    BASE="${current_dir%/}/${relative_dir#*/}"
fi

# Initialise variable default values
REDIS_CONF="$BASE/docker/redis.conf"
REDIS_PORT=6379
REDIS_PASSWORD=$(openssl rand -base64 20)
REDIS_DATA="/var/lib/redis"
SILENT=false

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
        -d | --data)
            REDIS_DATA="$2"
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

export REDIS_DATA=$REDIS_DATA
export REDIS_PASSWORD=$REDIS_PASSWORD
export REDIS_PORT=$REDIS_PORT

# Remove redis config if exist
if [ -f $REDIS_CONF ]; then
    sudo rm -f $REDIS_CONF
fi

# Download redis config
curl -o $REDIS_CONF https://raw.githubusercontent.com/redis/redis/unstable/redis.conf
! $SILENT && echo -e "\\033[32mRedis config downloaded\\033[0m"

OPTIONS=$([[ $SILENT == true ]] && echo "-s" || echo "")

# Set the password
$BASE/scripts/redis_set_password.sh -c $REDIS_CONF -a $REDIS_PASSWORD $OPTIONS

# Change binding
$BASE/scripts/redis_binding.sh -c $REDIS_CONF $OPTIONS

# Disable rdb
$BASE/scripts/redis_disable_rdb.sh -c $REDIS_CONF $OPTIONS

# Configure firewall
$BASE/scripts/redis_set_firewall.sh -p $REDIS_PORT $OPTIONS

# Build redis image
export REDIS_CONF=redis.conf
docker compose build redis &> /dev/null
! $SILENT && echo -e "\\033[32mRedis built\\033[0m"

# Clean temporary files
rm -f "$REDIS_CONF*"

# Ouput a guide to the user
! $SILENT && echo -e "\\033[32mUse the password '$REDIS_PASSWORD' when starting redis via redis_docker_start.sh\\033[0m"

if [[ $SILENT == true ]]; then
    echo "$REDIS_PASSWORD"
fi