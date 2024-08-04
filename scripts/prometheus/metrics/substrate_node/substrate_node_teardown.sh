#!/bin/bash

source ${BASH_SOURCE%/*}/substrate_node_variables.sh
source ${BASH_SOURCE%/*}/../../prometheus_variables.sh

# Step 5: Clean up Prometheus configuration
if [ -f "${PROMETHEUS_CONFIG_PATH}" ]; then
    sed -i '/- job_name: \"substrate_node\"/,/- job_name: \".*\"/{//!d};/- job_name: \"substrate_node\"/d' "$PROMETHEUS_CONFIG_PATH"
    sudo systemctl reload prometheus
    echo -e "\e[32m$SUBSTRATE_NODE_NAME removed from prometheus scraping\e[0m"
else
    echo "Prometheus configuration file not found at ${PROMETHEUS_CONFIG_PATH}."
    echo "Please ensure Prometheus is installed and the configuration file path is correct."
fi