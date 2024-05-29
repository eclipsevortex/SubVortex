#!/bin/bash

source ${BASH_SOURCE%/*}/prometheus_alert_variables.sh
source ${BASH_SOURCE%/*}/../../prometheus/prometheus_variables.sh

# Step 1: Stop and disable Alertmanager service
sudo systemctl stop alertmanager
sudo systemctl disable alertmanager
echo -e "\e[32m$PROMETHEUS_ALERT_NAME service stopped and disabled\e[0m"

# Step 2: Remove Alertmanager service file
sudo rm /etc/systemd/system/alertmanager.service
sudo systemctl daemon-reload
echo -e "\e[32m$PROMETHEUS_ALERT_NAME service file removed\e[0m"

# Step 3: Delete Alertmanager user and directories
sudo userdel alertmanager
echo -e "\e[32m$PROMETHEUS_ALERT_NAME user and directories removed\e[0m"

# Step 34: Remove Prometheus binaries
sudo rm -rf /usr/local/bin/alertmanager /usr/local/bin/amtool
echo -e "\e[32m$PROMETHEUS_ALERT_NAME binaries removed\e[0m"

# Step 5: Remove Alertmanager configuration and directories
sudo rm -rf /etc/alertmanager /var/lib/alertmanager
echo -e "\e[32m$PROMETHEUS_ALERT_NAME configuration and directories removed\e[0m"

# Step 6: Remove Alertmanager and alert rules configurations from Prometheus
if [ -f "${PROMETHEUS_CONFIG_PATH}" ]; then
    # Remove Alertmanager configuration
    sudo sed -i '/alerting:/,/targets:/c\alerting:\n  alertmanagers:\n    - static_configs:\n        - targets:' ${PROMETHEUS_CONFIG_PATH}
    
    # Remove alert rules file configuration
    ESCAPED_RULE_FILE=$(echo "$PROMETHEUS_ALERT_RULES_PATH" | sed 's/\//\\\//g')
    sudo sed -i "/^[[:space:]]*-[[:space:]]*\"${ESCAPED_RULE_FILE}\"[[:space:]]*$/d" ${PROMETHEUS_CONFIG_PATH}
    
    # Reload Prometheus service
    sudo systemctl reload prometheus
    echo -e "\e[32m$PROMETHEUS_ALERT_NAME configuration and alert rules removed from Prometheus, and Prometheus reloaded\e[0m"
else
    echo "Prometheus configuration file not found at ${PROMETHEUS_CONFIG_PATH}."
    echo "Please ensure Prometheus is installed and the configuration file path is correct."
fi
