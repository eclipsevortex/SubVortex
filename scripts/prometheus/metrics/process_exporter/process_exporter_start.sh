#!/bin/bash

source ${BASH_SOURCE%/*}/process_exporter_variables.sh

# Reload Systemd and start Node Exporter
sudo systemctl daemon-reload
sudo systemctl start process_exporter
sudo systemctl enable process_exporter
echo -e "\e[32m$PROCESS_EXPORTER_NAME started\e[0m"