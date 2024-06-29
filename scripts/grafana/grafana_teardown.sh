#!/bin/bash

# Stop Grafana service
sudo systemctl stop grafana-server

# Disable Grafana service
sudo systemctl disable grafana-server

# Uninstall Grafana
sudo apt remove --purge -y grafana

# Remove unused dependencies
sudo apt autoremove -y

# Remove Grafana repository
sudo add-apt-repository --remove "deb https://packages.grafana.com/oss/deb stable main"

# Remove Grafana GPG key
sudo apt-key del $(sudo apt-key list | grep -B 1 "Grafana" | head -n 1 | awk '{print $2}')

# Remove Grafana configuration and data directories
sudo rm -rf /etc/grafana /var/lib/grafana /var/log/grafana

echo -e '\e[32mGrafana and related files have been removed\e[0m'
