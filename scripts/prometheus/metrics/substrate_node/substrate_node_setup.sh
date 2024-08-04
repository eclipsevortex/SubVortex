#!/bin/bash

source ${BASH_SOURCE%/*}/substrate_node_variables.sh
source ${BASH_SOURCE%/*}/../../prometheus_variables.sh

# Step 7: Configure Prometheus to scrape Subtensor metrics
if [ -f "${PROMETHEUS_CONFIG_PATH}" ]; then
    sudo sed -i "/scrape_configs:/a\ \ - job_name: \"substrate_node\"\n\ \ \ \ static_configs:\n\ \ \ \ \ \ - targets: [\"localhost:$SUBSTRATE_PORT\"]" ${PROMETHEUS_CONFIG_PATH}
    sudo systemctl reload prometheus
else
    echo "Prometheus configuration file not found at ${PROMETHEUS_CONFIG_PATH}."
    echo "Please ensure Prometheus is installed and the configuration file path is correct."
fi
echo -e "\e[32m$SUBSTRATE_NODE_NAME added to prometheus scraping\e[0m"
