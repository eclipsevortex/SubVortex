#!/bin/bash

source ${BASH_SOURCE%/*}/../utils/machine.sh

function install_docker_on_linux() {
    if command -v docker &>/dev/null; then
        echo -e '\033[32mDocker already installed\033[0m'
        return
    fi
    
    # Add Docker's GPG Key:
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Set up the Stable Docker Repository:
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Update repository list
    sudo apt-get update
    
    # Install Docker Engine
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    echo -e '\033[32mDocker installed\033[0m'

    # Install pip package to prevent errors
    # Exception: TypeError: HTTPConnection.request() got an unexpected keyword argument 'chunked'
    pip install 'urllib3<2'
    echo -e '\033[32mDocker install packages to prevent exception\033[0m'
    
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

