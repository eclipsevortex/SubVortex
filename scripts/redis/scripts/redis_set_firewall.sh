#!/bin/bash

# This script disable snapshots and enable AOF for redis

show_help() {
cat << EOF
Usage: ${0##*/} [-p ARG] [-h] -- Disable snapshots and enable AOF for redis

    -p | --port ARG         port of the redis instance, default 6379
    -h | --help             display the help
EOF
}

OPTIONS="p:h"
LONGOPTIONS="port:,help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

REDIS_PORT=6379

while [ "$#" -gt 0 ]; do
    case "$1" in
        -p | --port)
            REDIS_PORT="$2"
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

# Check if UFW is installed
if ! command -v ufw &> /dev/null; then
    echo "UFW is not installed."
    exit 1
fi


# Ensure UFW is enabled
ufw status | grep -q inactive && ufw enable

# Deny all external traffic to port $REDIS_PORT
ufw deny $REDIS_PORT

# Allow all local traffic to port $REDIS_PORT
ufw allow from 127.0.0.1 to any port $REDIS_PORT

# Default behaviour 
# TODO: rewrite that firewall in order to avoid the following as it can be different from everyone
sudo ufw default allow incoming
sudo ufw default allow outgoing

# Reload UFW to apply changes
ufw reload

# Notification
echo -e "\\033[32mFirewall updated\\033[0m"
