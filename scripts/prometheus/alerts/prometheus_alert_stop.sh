#!/bin/bash

source ${BASH_SOURCE%/*}/prometheus_alert_variables.sh

# Stop Prometheus service and disable it from starting on boot
sudo systemctl stop alertmanager
sudo systemctl disable alertmanager
sudo systemctl daemon-reload
echo -e "\e[32m$PROMETHEUS_ALERT_NAME stopped\e[0m"