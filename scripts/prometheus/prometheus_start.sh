#!/bin/bash

source ${BASH_SOURCE%/*}/prometheus_variables.sh

# Enable Prometheus to start on boot and start Prometheus service
sudo systemctl daemon-reload
sudo systemctl start prometheus
sudo systemctl enable prometheus
echo -e "\e[32m$PROMETHEUS_NAME started\e[0m"