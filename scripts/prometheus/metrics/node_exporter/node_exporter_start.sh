#!/bin/bash

source ${BASH_SOURCE%/*}/node_exporter_variables.sh

# Reload Systemd and start Node Exporter
sudo systemctl daemon-reload
sudo systemctl start node_exporter
sudo systemctl enable node_exporter
echo -e "\e[32m$NODE_EXPORTER_NAME started\e[0m"