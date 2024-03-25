#!/bin/bash

source ${BASH_SOURCE%/*}/../../utils/machine.sh

function uninstall_redis_linux() {
    # Remove Redis GPG key in binary format
    if [ -f /usr/share/keyrings/redis-archive-keyring.gpg ]; then
        sudo rm /usr/share/keyrings/redis-archive-keyring.gpg
    fi

    # Remove the Redis package and its configuration files from the system.
    sudo apt-get remove --purge redis-server -y
    
    # Remove any automatically installed packages that are no longer required.
    sudo apt-get autoremove -y
    
    # Remove Redis configuration files and data directory.
    sudo rm -rf /etc/redis /var/lib/redis
}

function uninstall_redis_macos() {
    brew uninstall redis
}

os=$(get_os)

if [[ $os == "linux" ]]; then
    uninstall_redis_linux
else
    uninstall_redis_macos
fi