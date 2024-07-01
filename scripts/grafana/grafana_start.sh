#!/bin/bash

source ${BASH_SOURCE%/*}/grafana_variables.sh

sudo iptables -C INPUT -p tcp --dport $GRAFANA_PORT -j ACCEPT &> /dev/null
if [ $? -eq 1 ]; then
    # Add an allow rule
    sudo iptables -A INPUT -p tcp --dport $GRAFANA_PORT -j ACCEPT
fi

# Enable Grafana to start on boot and start Grafana service
sudo systemctl daemon-reload
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
echo -e "\e[32m$GRAFANA_NAME started\e[0m"
