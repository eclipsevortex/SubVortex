#!/bin/bash

# Create an allow rule
sudo iptables -A INPUT -p tcp --dport 3000 -j ACCEPT

# Enable Grafana to start on boot and start Grafana service
sudo systemctl daemon-reload
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
echo -e '\e[32mPrometheus reloaded\e[0m'
