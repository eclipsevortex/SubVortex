#!/bin/bash

source ${BASH_SOURCE%/*}/prometheus_variables.sh

# Stop Prometheus service and disable it from starting on boot
sudo systemctl stop prometheus
sudo systemctl disable prometheus
sudo systemctl daemon-reload
echo -e "\e[32m$PROMETHEUS_NAME stopped\e[0m"