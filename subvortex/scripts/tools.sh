#!/bin/bash

function install_npm() {
    # Check pm2 is already installed
    if command -v npm &> /dev/null; then
        return
    fi
    
    # Install npm
    sudo apt-get install -y nodejs npm
}

function install_pm2() {
    # Check pm2 is already installed
    if command -v pm2 &> /dev/null; then
        return
    fi
    
    # Install pre-requisites
    install_npm
    
    # Install pm2
    sudo npm i -g pm2
}