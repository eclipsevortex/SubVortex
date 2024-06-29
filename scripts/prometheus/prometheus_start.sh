#!/bin/bash

# Enable Prometheus to start on boot and start Prometheus service
sudo systemctl daemon-reload
sudo systemctl start prometheus
sudo systemctl enable prometheus
echo -e '\e[32mPrometheus reloaded\e[0m'