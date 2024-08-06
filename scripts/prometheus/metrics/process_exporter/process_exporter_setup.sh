#!/bin/bash

source ${BASH_SOURCE%/*}/process_exporter_variables.sh
source ${BASH_SOURCE%/*}/../../prometheus_variables.sh

# Update package index
sudo apt update

# Step 1: Download Process Exporter
wget https://github.com/ncabatoff/process-exporter/releases/download/v${PROCESS_EXPORTER_VERSION}/process-exporter-${PROCESS_EXPORTER_VERSION}.linux-amd64.tar.gz
echo -e "\e[32m$PROCESS_EXPORTER_NAME downloaded\e[0m"

# Step 2: Extract the Process Exporter archive
tar xvfz process-exporter-${PROCESS_EXPORTER_VERSION}.linux-amd64.tar.gz
echo -e "\e[32m$PROCESS_EXPORTER_NAME extracted\e[0m"

# Step 3: Move the binary to /usr/local/bin
sudo mv process-exporter-${PROCESS_EXPORTER_VERSION}.linux-amd64/process-exporter /usr/local/bin/
echo -e "\e[32m$PROCESS_EXPORTER_NAME binary moved\e[0m"

# Step 4: Create a Process Exporter user
sudo useradd --no-create-home --shell /bin/false ${PROCESS_EXPORTER_USER}
echo -e "\e[32m$PROCESS_EXPORTER_NAME user created\e[0m"

# Step 5: Create Process Exporter configuration file
sudo mkdir -p /etc/process-exporter
sudo tee /etc/process-exporter/config.yml > /dev/null <<EOF
process_names:
  - name: "{{.Comm}}"
    cmdline:
    - '.*'
EOF
echo -e "\e[32m$PROCESS_EXPORTER_NAME configuration file created\e[0m"

# Step 6: Create a Systemd service file for Process Exporter
sudo tee /etc/systemd/system/process_exporter.service > /dev/null <<EOF
[Unit]
Description=Process Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=${NODE_EXPORTER_USER}
Group=${NODE_EXPORTER_USER}
Type=simple
ExecStart=/usr/local/bin/process-exporter --config.path /etc/process-exporter/config.yml

[Install]
WantedBy=multi-user.target
EOF
echo -e "\e[32m$PROCESS_EXPORTER_NAME systemd service configured\e[0m"

# Step 7: Configure Prometheus to scrape Process Exporter metrics
if [ -f "${PROMETHEUS_CONFIG_PATH}" ]; then
    sudo sed -i "/scrape_configs:/a\ \ - job_name: \"process_exporter\"\n\ \ \ \ static_configs:\n\ \ \ \ \ \ - targets: [\"localhost:$PROCESS_EXPORTER_PORT\"]" ${PROMETHEUS_CONFIG_PATH}
    sudo systemctl reload prometheus
else
    echo "Prometheus configuration file not found at ${PROMETHEUS_CONFIG_PATH}."
    echo "Please ensure Prometheus is installed and the configuration file path is correct."
fi
echo -e "\e[32m$PROCESS_EXPORTER_NAME added to prometheus scraping\e[0m"

# Step 8: Cleanup
rm -rf process_exporter-${PROCESS_EXPORTER_VERSION}.linux-amd64.tar.gz process_exporter-${PROCESS_EXPORTER_VERSION}.linux-amd64
echo -e "\e[32m$PROCESS_EXPORTER_NAME cleaned up\e[0m"
