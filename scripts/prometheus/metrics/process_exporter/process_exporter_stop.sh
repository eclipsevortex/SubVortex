#!/bin/bash

source ${BASH_SOURCE%/*}/process_exporter_variables.sh

# Reload Systemd and start Node Exporter
sudo systemctl stop process_exporter
sudo systemctl disable process_exporter
sudo systemctl daemon-reload
echo -e "\e[32m$PROCESS_EXPORTER_NAME stoped\e[0m"
