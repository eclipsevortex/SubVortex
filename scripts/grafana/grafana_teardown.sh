#!/bin/bash

source ${BASH_SOURCE%/*}/grafana_variables.sh

# Uninstall Grafana
sudo apt remove --purge -y grafana
echo -e "\e[32m$GRAFANA_NAME uninstalled\e[0m"

# Remove unused dependencies
sudo apt autoremove -y
echo -e "\e[32m$GRAFANA_NAME dependencies uninstalled\e[0m"

# Remove Grafana repository
sudo add-apt-repository --remove "deb https://packages.grafana.com/oss/deb stable main"
echo -e "\e[32m$GRAFANA_NAME repository removed\e[0m"

# Remove Grafana GPG key
sudo apt-key del $(sudo apt-key list | grep -B 1 "Grafana" | head -n 1 | awk '{print $2}')
echo -e "\e[32m$GRAFANA_NAME GPG key removed\e[0m"

# Remove Grafana configuration and data directories
sudo rm -rf /etc/grafana /var/lib/grafana /var/log/grafana
echo -e "\e[32m$GRAFANA_NAME configuration removed\e[0m"
