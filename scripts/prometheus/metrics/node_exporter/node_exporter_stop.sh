#!/bin/bash

source ${BASH_SOURCE%/*}/node_exporter_variables.sh

# Reload Systemd and start Node Exporter
sudo systemctl stop node_exporter
sudo systemctl disable node_exporter
sudo systemctl daemon-reload
echo -e "\e[32m$NODE_EXPORTER_NAME stoped\e[0m"
