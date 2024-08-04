#!/bin/bash

source ${BASH_SOURCE%/*}/prometheus_alert_variables.sh

# Enable Alertmanager to start on boot and start Alertmanager service
sudo systemctl daemon-reload
sudo systemctl start alertmanager
sudo systemctl enable alertmanager
echo -e "\e[32m$PROMETHEUS_ALERT_NAME started\e[0m"