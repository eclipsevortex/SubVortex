#!/bin/bash

echo ${BASH_SOURCE%/*}

source ${BASH_SOURCE%/*}/../utils/machine.sh

function uninstall_on_linux() {
    # Remove Docker's GPG Key:
    if [ -f /usr/share/keyrings/docker-archive-keyring.gpg ]; then
        sudo rm /usr/share/keyrings/docker-archive-keyring.gpg
    fi

    # Remove Docker packages
    sudo apt-get purge docker-ce docker-ce-cli containerd.io
    echo -e '\033[32mRemove docker package\033[0m'

    # Remove Docker images, containers, volumes, and networks
    sudo rm -rf /var/lib/docker
    echo -e '\033[32mUninstall docker\033[0m'

    # Remove the user to the docker group
    sudo gpasswd -d $USER docker
    echo -e '\033[32mDocker user removed\033[0m'

    # Remove the docker group
    sudo groupdel docker
    echo -e '\033[32mDocker group removed\033[0m'

    # Uninstall docker compose
    sudo apt-get remove docker-compose
    echo -e '\033[32mUninstall docker compose\033[0m'

    # Remove docker binary
    result=$(command -v docker)
    if [[ ! -z $result ]]; then
        rm -rf $result
        echo -e '\033[32mDocker binary removed\033[0m'
    fi

    # Remove docker compose binary
    result=$(command -v docker-compose)
    if [[ ! -z $result ]]; then
        rm -rf $result
        echo -e '\033[32mDocker compose binary removed\033[0m'
    fi
}

os=$(get_os)

echo $os

if [[ $os == "linux" ]]; then
    uninstall_on_linux
else
    echo -e '\033[38;5;208mRefer to the doc to uninstall docker on your system.\033[0m'
fi

