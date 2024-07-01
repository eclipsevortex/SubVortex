#!/bin/bash

source ${BASH_SOURCE%/*}/grafana_variables.sh

# Update package index
sudo apt update

# Install required dependencies
sudo apt install -y apt-transport-https software-properties-common wget
echo -e "\e[32m$GRAFANA_NAME dependencies installed\e[0m"

# Import Grafana GPG key
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo -e "\e[32m$GRAFANA_NAME GPG key imported\e[0m"

# Add Grafana repository
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
echo -e "\e[32m$GRAFANA_NAME repository added\e[0m"

# Update package index again
sudo apt update

# Install Grafana
sudo apt install -y grafana
echo -e "\e[32m$GRAFANA_NAME installed\e[0m"
