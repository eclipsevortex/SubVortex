#!/bin/bash

source ${BASH_SOURCE%/*}/grafana_variables.sh

sudo iptables -C INPUT -p tcp --dport $GRAFANA_PORT -j ACCEPT &> /dev/null
if [ $? -eq 0 ]; then
    # Delete an allow rule
    sudo iptables -D INPUT -p tcp --dport $GRAFANA_PORT -j ACCEPT
fi

# Stop Grafana service and disable it from starting on boot
sudo systemctl stop grafana-server
sudo systemctl disable grafana-server
sudo systemctl daemon-reload
echo -e "\e[32m$GRAFANA_NAME stoped\e[0m"