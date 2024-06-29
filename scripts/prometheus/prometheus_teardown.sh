#!/bin/bash

# Step 1: Stop and disable Prometheus service
./prometheus_stop.sh

# Step 2: Remove Prometheus binaries
sudo rm -f /usr/local/bin/prometheus /usr/local/bin/promtool
echo -e '\e[31mPrometheus binaries removed\e[0m'

# Step 3: Remove Prometheus configuration and directories
sudo rm -rf /etc/prometheus /var/lib/prometheus
echo -e '\e[31mPrometheus configuration and directories removed\e[0m'

# Step 4: Remove Prometheus user
sudo userdel prometheus
echo -e '\e[31mPrometheus user removed\e[0m'

# Step 5: Remove Prometheus systemd service file
sudo rm -f /etc/systemd/system/prometheus.service
sudo systemctl daemon-reload
echo -e '\e[31mPrometheus systemd service file removed\e[0m'

# Step 6: Optional - remove downloaded tarball and extracted directory if they exist
rm -f prometheus-2.30.3.linux-amd64.tar.gz
rm -rf prometheus-2.30.3.linux-amd64
echo -e '\e[31mPrometheus tarball and extracted directory removed (if existed)\e[0m'
