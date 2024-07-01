#!/bin/bash

source ${BASH_SOURCE%/*}/node_exporter_variables.sh

sudo iptables -C INPUT -p tcp --dport $NODE_EXPORTER_PORT -j ACCEPT &> /dev/null
if [ $? -eq 0 ]; then
    # Remove an allow rule
    sudo iptables -D INPUT -p tcp --dport $NODE_EXPORTER_PORT -j ACCEPT
fi

# Reload Systemd and start Node Exporter
sudo systemctl stop node_exporter
sudo systemctl disable node_exporter
sudo systemctl daemon-reload
echo -e "\e[32m$NODE_EXPORTER_NAME stoped\e[0m"
