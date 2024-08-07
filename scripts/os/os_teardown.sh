#!/bin/bash

show_help() {
cat << EOF
Usage: ${0##*/} [-t ARG] [-h] -- Install os packages for miner or validator
    -t | --type ARG         type of process you want to run (miner or validator), default miner
    -h | --help             display the help
EOF
}

OPTIONS="t:ih"
LONGOPTIONS="type:,:help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

TYPE='miner'

while [ "$#" -gt 0 ]; do
    case "$1" in
        -t | --type)
            TYPE="$2"
            shift 2
        ;;
        *)
            echo "Unrecognized option '$1'"
            exit 1
        ;;
    esac
done

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

is_package_installed() {
    dpkg-query -W -f='${Status}' "$1" 2>/dev/null | grep -c "ok installed"
}

uninstall_package() {
    local package_name=$1
    
    if [ $(is_package_installed "$package_name") -eq 1 ]; then
        sudo apt-get remove --purge -y "$package_name"
        if [ $(is_package_installed "$package_name") -eq 0 ]; then
            echo -e "\\e[32m$package_name uninstalled\\e[0m"
        else
            echo -e "\\e[31m$package_name uninstallation failed\\e[0m"
        fi
    fi
}

# Linux specific uninstallations
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    uninstall_package "git"
    uninstall_package "python3-pip"
    uninstall_package "libnetfilter-queue-dev"
    
    if [[ "$TYPE" == "miner" ]]; then
        # Dependencies to use nfqueue
        uninstall_package "build-essential"
        uninstall_package "python3-dev"
    fi
fi

# For macOS and Windows, you would need different commands to uninstall packages
# MacOS
# if [[ "$OSTYPE" == "darwin"* ]]; then
#     # Homebrew uninstall commands would go here
# fi

# Windows
# if [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
#     # Winget or other Windows uninstall commands would go here
# fi
