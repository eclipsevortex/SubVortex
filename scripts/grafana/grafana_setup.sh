#!/bin/bash

# Update package index
sudo apt update

# Install required dependencies
sudo apt install -y apt-transport-https software-properties-common wget

# Import Grafana GPG key
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -

# Add Grafana repository
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"

# Update package index again
sudo apt update

# Install Grafana
sudo apt install -y grafana