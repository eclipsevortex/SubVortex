#!/bin/bash

source ${BASH_SOURCE%/*}/node_exporter_variables.sh

# Step 1: Remove the Node Exporter systemd service file
sudo rm /etc/systemd/system/node_exporter.service
sudo systemctl daemon-reload
echo -e "\e[31m$NODE_EXPORTER_NAME systemd service file removed\e[0m"

# Step 2: Remove the Node Exporter user
sudo userdel -r ${NODE_EXPORTER_USER}
echo -e "\e[31m$NODE_EXPORTER_NAME user removed\e[0m"

# Step 3: Remove the Node Exporter binary
sudo rm /usr/local/bin/node_exporter
echo -e "\e[31m$NODE_EXPORTER_NAME binary removed\e[0m"

# Step 4: Clean up Prometheus configuration
if [ -f "${PROMETHEUS_CONFIG_PATH}" ]; then
    sudo sed -i "/- job_name: 'node_exporter'/,+3d" ${PROMETHEUS_CONFIG_PATH}
    sudo systemctl reload prometheus
    echo -e "\e[31m$NODE_EXPORTER_NAME removed from prometheus scraping\e[0m"
else
    echo "Prometheus configuration file not found at ${PROMETHEUS_CONFIG_PATH}."
    echo "Please ensure Prometheus is installed and the configuration file path is correct."
fi