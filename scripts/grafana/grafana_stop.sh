#!/bin/bash

# Delete an allow rule
sudo iptables -D INPUT -p tcp --dport 3000 -j ACCEPT

# Stop Grafana service and disable it from starting on boot
sudo systemctl daemon-reload
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
echo -e '\e[Grafana stopped and disabled\e[0m'