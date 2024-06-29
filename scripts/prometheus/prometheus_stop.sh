#!/bin/bash

# Stop Prometheus service and disable it from starting on boot
sudo systemctl stop prometheus
sudo systemctl disable prometheus
sudo systemctl daemon-reload
echo -e '\e[32mPrometheus stopped and disabled\e[0m'