#!/bin/bash

echo ${BASH_SOURCE%/*}

source ${BASH_SOURCE%/*}/../utils/machine.sh

function install_on_linux() {
    ## Add Docker's GPG Key:
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    ## Set up the Stable Docker Repository:
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    ## Update repository list
    sudo apt-get update
    
    ## Install Docker Engine
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    echo -e '\033[32mDocker installed\033[0m'
    
    ## Add the user to the docker group
    sudo usermod -aG docker $USER
    echo -e '\033[32mDocker user created\033[0m'
    
    # Install docker compose
    sudo apt-get install -y docker-compose
    echo -e '\033[32mDocker compose installed\033[0m'

    # Apply the group membership (you may need to log out and log back in for the group to be recognized):
    # IMPORTANT: Be sure the following is the last instruction to execute because it will starts a new shell session 
    # with the docker group privileges
    newgrp docker
    echo -e '\033[32mGroup membership applied\033[0m'

    # Start docker if not started
    if ! docker info &> /dev/null; then
        sudo systemctl start docker
        echo -e '\033[32mDocker started\033[0m'
    fi 
}

os=$(get_os)

if [[ $os == "linux" ]]; then
    install_on_linux
else
    echo -e '\033[38;5;208mRefer to the doc to install docker on your system.\033[0m'
fi

