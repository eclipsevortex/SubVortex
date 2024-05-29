#!/bin/bash

source ${BASH_SOURCE%/*}/node_exporter_variables.sh
source ${BASH_SOURCE%/*}/../../prometheus_variables.sh

# Step 1: Remove the Node Exporter systemd service file
sudo rm -f /etc/systemd/system/node_exporter.service
sudo systemctl daemon-reload
echo -e "\e[32m$NODE_EXPORTER_NAME systemd service file removed\e[0m"

# Step 2: Remove the Node Exporter user
sudo userdel ${NODE_EXPORTER_USER}
echo -e "\e[32m$NODE_EXPORTER_NAME user removed\e[0m"

# Step 3: Remove the Node Exporter binary
sudo rm -rf /usr/local/bin/node_exporter
echo -e "\e[32m$NODE_EXPORTER_NAME binary removed\e[0m"

# Step 4: Clean up Prometheus configuration
if [ -f "${PROMETHEUS_CONFIG_PATH}" ]; then
    sed -i '/- job_name: \"node_exporter\"/,/- job_name: \".*\"/{//!d};/- job_name: \"node_exporter\"/d' "$PROMETHEUS_CONFIG_PATH"
    sudo systemctl reload prometheus
    echo -e "\e[32m$NODE_EXPORTER_NAME removed from prometheus scraping\e[0m"
else
    echo "Prometheus configuration file not found at ${PROMETHEUS_CONFIG_PATH}."
    echo "Please ensure Prometheus is installed and the configuration file path is correct."
fi