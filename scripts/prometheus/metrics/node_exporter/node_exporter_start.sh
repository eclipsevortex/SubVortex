#!/bin/bash

source ${BASH_SOURCE%/*}/node_exporter_variables.sh

sudo iptables -C INPUT -p tcp --dport $NODE_EXPORTER_PORT -j ACCEPT &> /dev/null
if [ $? -eq 1 ]; then
    # Add an allow rule
    sudo iptables -A INPUT -p tcp --dport $NODE_EXPORTER_PORT -j ACCEPT
fi

# Reload Systemd and start Node Exporter
sudo systemctl daemon-reload
sudo systemctl start node_exporter
sudo systemctl enable node_exporter
echo -e "\e[32m$NODE_EXPORTER_NAME started\e[0m"