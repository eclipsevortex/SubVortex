#!/bin/bash

source ${BASH_SOURCE%/*}/prometheus_variables.sh

# Update package index
sudo apt update

# Step 1: Download Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.30.3/prometheus-2.30.3.linux-amd64.tar.gz
echo -e "\e[32m$PROMETHEUS_NAME downloaded\e[0m"

# Step 2: Extract Prometheus archive
tar xvfz prometheus-2.30.3.linux-amd64.tar.gz
echo -e "\e[32m$PROMETHEUS_NAME extracted\e[0m"

# Step 3: Move Prometheus binaries to /usr/local/bin
sudo mv prometheus-2.30.3.linux-amd64/{prometheus,promtool} /usr/local/bin/
echo -e "\e[32m$PROMETHEUS_NAME binary moved\e[0m"

# Step 4: Move Prometheus configuration directory to /etc/prometheus
sudo mkdir -p /etc/prometheus
sudo mv prometheus-2.30.3.linux-amd64/{prometheus.yml,console_libraries,consoles} /etc/prometheus/
echo -e "\e[32m$PROMETHEUS_NAME configuration moved\e[0m"

# Step 5: Create Prometheus user and directories
sudo useradd --no-create-home --shell /bin/false prometheus
mkdir /var/lib/prometheus
sudo chown -R prometheus:prometheus /etc/prometheus /usr/local/bin/prometheus /usr/local/bin/promtool /var/lib/prometheus
echo -e "\e[32m$PROMETHEUS_NAME user/directories created\e[0m"

# Step 7: Configure systemd service for Prometheus
sudo tee /etc/systemd/system/prometheus.service > /dev/null <<EOF
[Unit]
Description=Prometheus Server
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
    --config.file=/etc/prometheus/prometheus.yml \
    --storage.tsdb.path=/var/lib/prometheus \
    --web.console.templates=/etc/prometheus/consoles \
    --web.console.libraries=/etc/prometheus/console_libraries
ExecReload=/bin/kill -HUP \$MAINPID

[Install]
WantedBy=multi-user.target
EOF
echo -e "\e[32m$PROMETHEUS_NAME systemd service configured\e[0m"

# Step 8: Clean up
rm prometheus-2.30.3.linux-amd64.tar.gz
rm -rf prometheus-2.30.3.linux-amd64
echo -e "\e[32m$PROMETHEUS_NAME cleaned up\e[0m"
