#!/bin/bash

source ${BASH_SOURCE%/*}/../utils/machine.sh

function install_docker_on_linux() {
    if command -v docker &>/dev/null; then
        echo -e '\033[32mDocker already installed\033[0m'
        return
    fi

    # Add Docker's official GPG key:
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    # Add the repository to Apt sources:
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update

    # Install the latest version
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Create the docker group
    sudo groupadd docker
    echo -e '\033[32mDocker group created\033[0m'
    
    # Add the user to the docker group
    sudo usermod -aG docker $USER
    echo -e '\033[32mDocker user created\033[0m'
    
    # Apply the group membership (you may need to log out and log back in for the group to be recognized):
    (newgrp docker &)
    echo -e '\033[32mGroup membership applied\033[0m'
}

function install_docker_compose_on_linux() {
    if command -v docker-compose &>/dev/null; then
        echo -e '\033[32mDocker compose already installed\033[0m'
        return
    fi
    
    # Install docker compose
    sudo apt-get install -y docker-compose
    echo -e '\033[32mDocker compose installed\033[0m'
}

os=$(get_os)


if [[ $os == "linux" ]]; then
    # Install docker
    install_docker_on_linux
    
    # Install docker compose
    install_docker_compose_on_linux
else
    echo -e '\033[38;5;208mRefer to the doc to install docker on your system.\033[0m'
fi

