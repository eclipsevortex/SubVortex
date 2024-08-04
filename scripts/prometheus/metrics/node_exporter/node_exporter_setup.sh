#!/bin/bash

source ${BASH_SOURCE%/*}/node_exporter_variables.sh
source ${BASH_SOURCE%/*}/../../prometheus_variables.sh

# Update package index
sudo apt update

# Step 1: Download Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v${NODE_EXPORTER_VERSION}/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
echo -e "\e[32m$NODE_EXPORTER_NAME downloaded\e[0m"

# Step 2: Extract the Node Exporter archive
tar xvfz node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
echo -e "\e[32m$NODE_EXPORTER_NAME extracted\e[0m"

# Step 3: Move the binary to /usr/local/bin
sudo mv node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64/node_exporter /usr/local/bin/
echo -e "\e[32m$NODE_EXPORTER_NAME binary moved\e[0m"

# Step 4: Create a Node Exporter user
sudo useradd -r --shell /bin/false ${NODE_EXPORTER_USER}
echo -e "\e[32m$NODE_EXPORTER_NAME user created\e[0m"

# Step 5: Create a Systemd service file for Node Exporter
sudo tee /etc/systemd/system/node_exporter.service > /dev/null <<EOF
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=${NODE_EXPORTER_USER}
Group=${NODE_EXPORTER_USER}
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF
echo -e "\e[32m$NODE_EXPORTER_NAME systemd service configured\e[0m"

# Step 6: Configure Prometheus to scrape Node Exporter metrics
if [ -f "${PROMETHEUS_CONFIG_PATH}" ]; then
    sudo sed -i "/scrape_configs:/a\ \ - job_name: \"node_exporter\"\n\ \ \ \ static_configs:\n\ \ \ \ \ \ - targets: [\"localhost:$NODE_EXPORTER_PORT\"]" ${PROMETHEUS_CONFIG_PATH}
    sudo systemctl reload prometheus
else
    echo "Prometheus configuration file not found at ${PROMETHEUS_CONFIG_PATH}."
    echo "Please ensure Prometheus is installed and the configuration file path is correct."
fi
echo -e "\e[32m$NODE_EXPORTER_NAME added to prometheus scraping\e[0m"

# Step 7: Cleanup
rm -rf node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64
echo -e "\e[32m$NODE_EXPORTER_NAME cleaned up\e[0m"
