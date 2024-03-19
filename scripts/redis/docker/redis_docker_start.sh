#!/bin/bash

# This script start the redis installed as docker container

show_help() {
cat << EOF
Usage: ${0##*/} [-c ARG] [-p ARG] [-a ARG] [-d ARG] [-h] -- Start redis as docker container

    -c | --config ARG       path of the redis.conf, default redis.conf
    -p | --port ARG         port of the redis instance, default 6379
    -a | --password ARG     password to protect redis instance
    -d | --data ARG         directory to store redis data
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

REDIS_CONF=redis.conf
REDIS_PORT=6379
REDIS_DATA="/var/lib/redis"

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

if [[ -z $REDIS_PASSWORD ]]; then
    echo -e "\\033[31mProvide the redis password generated during the installation. Run with -h to display the help.\\033[0m"
    exit 1
fi

export REDIS_CONF=$REDIS_CONF
export REDIS_DATA=$REDIS_DATA
export REDIS_PASSWORD=$REDIS_PASSWORD
export REDIS_PORT=$REDIS_PORT

# Start redis container
docker-compose up -d redis