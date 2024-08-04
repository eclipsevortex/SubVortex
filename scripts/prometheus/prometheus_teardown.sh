#!/bin/bash

source ${BASH_SOURCE%/*}/prometheus_variables.sh

# Step 1: Remove Prometheus systemd service file
sudo rm -f /etc/systemd/system/prometheus.service
sudo systemctl daemon-reload
echo -e "\e[32m$PROMETHEUS_NAME systemd service file removed\e[0m"

# Step 2: Remove Prometheus user
sudo userdel prometheus
echo -e "\e[32m$PROMETHEUS_NAME user removed\e[0m"

# Step 3: Remove Prometheus binaries
sudo rm -rf /usr/local/bin/prometheus /usr/local/bin/promtool
echo -e "\e[32m$PROMETHEUS_NAME binaries removed\e[0m"

# Step 4: Remove Prometheus configuration and directories
sudo rm -rf /etc/prometheus /var/lib/prometheus
echo -e "\e[32m$PROMETHEUS_NAME configuration and directories removed\e[0m"

