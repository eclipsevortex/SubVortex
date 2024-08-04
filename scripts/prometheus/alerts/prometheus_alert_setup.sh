#!/bin/bash

source ${BASH_SOURCE%/*}/prometheus_alert_variables.sh
source ${BASH_SOURCE%/*}/../../prometheus/prometheus_variables.sh

ALERTMANAGER_HOST="localhost:$PROMETHEUS_ALERT_PORT"

show_help() {
cat << EOF
Usage: ${0##*/} [-o ARG] [-p ARG] [-f ARG] [-t ARG] [-h] -- Install Prometheus Alert Manager

    -o | --host ARG     SMTP server to send emails through (e.g., smtp.gmail.com:587) (default: smtp.gmail.com:587)
    -p | --password ARG App password for the email account (ensure you use an app-specific password)
    -f | --from ARG     Email address that will appear as the sender of alerts (default: subvortex@gmail.com")
    -t | --to ARG       Email address where the alerts will be sent
    -h | --help         Display this help message
EOF
}

OPTIONS="o:p:f:t:h"
LONGOPTIONS="host:,password:,from:,to:,help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

EMAIL_HOST="smtp.gmail.com:587"
EMAIL_PASSSWORD=""
EMAIL_FROM="subvortex@gmail.com"
EMAIL_TO=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        -o | --host)
            EMAIL_HOST="$2"
            shift 2
        ;;
        -p | --password)
            EMAIL_PASSSWORD="$2"
            shift 2
        ;;
        -f | --from)
            EMAIL_FROM="$2"
            shift 2
        ;;
        -t | --to)
            EMAIL_TO="$2"
            shift 2
        ;;
        -h | --help)
            show_help
            exit 0
        ;;
        *)
            echo "Unrecognized option '$1'"
            exit 1
        ;;
    esac
done

# Prompt for password if not provided
if [ -z "$EMAIL_PASSSWORD" ]; then
    read -s -p "Enter email password: " EMAIL_PASSSWORD
    echo
fi

if [[ -z $EMAIL_HOST ]] || [[ -z $EMAIL_PASSSWORD ]] || [[ -z $EMAIL_FROM ]] || [[ -z $EMAIL_TO ]]; then
    echo -e "\\033[31mThe email arguments are all mandatory. Run with -h to display the help.\\033[0m"
    exit 1
fi

# Update package index
sudo apt update

# Step 1: Download Alertmanager
wget https://github.com/prometheus/alertmanager/releases/download/v0.25.0/alertmanager-0.25.0.linux-amd64.tar.gz
echo -e "\e[32m$PROMETHEUS_ALERT_NAME downloaded\e[0m"

# Step 2: Extract Alertmanager archive
tar xvfz alertmanager-0.25.0.linux-amd64.tar.gz
echo -e "\e[32m$PROMETHEUS_ALERT_NAME extracted\e[0m"

# Step 3: Move Alertmanager binaries to /usr/local/bin
sudo mv alertmanager-0.25.0.linux-amd64/alertmanager /usr/local/bin/
sudo mv alertmanager-0.25.0.linux-amd64/amtool /usr/local/bin/
echo -e "\e[32m$PROMETHEUS_ALERT_NAME binary moved\e[0m"

# Step 4: Create Alertmanager configuration directory
sudo mkdir -p /etc/alertmanager
echo -e "\e[32m$PROMETHEUS_ALERT_NAME configuration directory created\e[0m"

# Step 5: Create Alertmanager user and directories
sudo useradd --no-create-home --shell /bin/false alertmanager
mkdir /var/lib/alertmanager
sudo chown alertmanager:alertmanager /usr/local/bin/alertmanager /usr/local/bin/amtool
sudo chown -R alertmanager:alertmanager /etc/alertmanager /var/lib/alertmanager
echo -e "\e[32m$PROMETHEUS_ALERT_NAME user/directories created\e[0m"

# Step 6: Create Alertmanager configuration file
echo -e "\e[32m$PROMETHEUS_ALERT_NAME configuration file created\e[0m"
sudo tee /etc/alertmanager/alertmanager.yml > /dev/null <<EOF
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h
  receiver: 'email'

receivers:
- name: 'email'
  email_configs:
  - to: '$EMAIL_TO'
    from: '$EMAIL_FROM'
    smarthost: '$EMAIL_HOST'
    auth_username: '$EMAIL_TO'
    auth_identity: '$EMAIL_TO'
    auth_password: '$EMAIL_PASSSWORD'
EOF

# Step 7: Set up Alertmanager as a service
sudo tee /etc/systemd/system/alertmanager.service > /dev/null <<EOF
[Unit]
Description=Alertmanager
Wants=network-online.target
After=network-online.target

[Service]
User=alertmanager
Group=alertmanager
Type=simple
ExecStart=/usr/local/bin/alertmanager \
  --config.file=/etc/alertmanager/alertmanager.yml \
  --storage.path=/var/lib/alertmanager/ \
  --cluster.advertise-address=$(hostname -I | awk '{print $1}'):9093

[Install]
WantedBy=multi-user.target
EOF
echo -e "\e[32m$PROMETHEUS_ALERT_NAME systemd service configured\e[0m"

# Step 8: Copy the rules
cp $HOME/SubVortex/scripts/prometheus/alerts/prometheus_alert_rules.yml $PROMETHEUS_ALERT_RULES_PATH
echo -e "\e[32m$PROMETHEUS_ALERT_NAME rules copied\e[0m"

# Step 9: Configure Prometheus to scrape Node Exporter metrics
if [ -f "${PROMETHEUS_CONFIG_PATH}" ]; then
    # Add Alertmanager configuration if commented out or missing
    if grep -q "# - alertmanager:9093" "${PROMETHEUS_CONFIG_PATH}"; then
        sudo sed -i "/alerting:/,/targets:/c\alerting:\n  alertmanagers:\n    - static_configs:\n        - targets: [\"localhost:$PROMETHEUS_ALERT_PORT\"]" ${PROMETHEUS_CONFIG_PATH}
        elif ! grep -q "${ALERTMANAGER_HOST}" "${PROMETHEUS_CONFIG_PATH}"; then
        sudo sed -i "/alertmanagers:/a\    - static_configs:\n        - targets: ['${ALERTMANAGER_HOST}']" ${PROMETHEUS_CONFIG_PATH}
    fi
    
    # Add alert rules file if commented out or missing
    if grep -q "# - \"first_rules.yml\"" "${PROMETHEUS_CONFIG_PATH}"; then
        sudo sed -i "s|# - \"first_rules.yml\"|  - \"${PROMETHEUS_ALERT_RULES_PATH}\"|" ${PROMETHEUS_CONFIG_PATH}
        elif ! grep -q "${PROMETHEUS_ALERT_RULES_PATH}" "${PROMETHEUS_CONFIG_PATH}"; then
        sudo sed -i "/rule_files:/a\  - \"${PROMETHEUS_ALERT_RULES_PATH}\"" ${PROMETHEUS_CONFIG_PATH}
    fi
    
    # Reload Prometheus service
    sudo systemctl reload prometheus
    echo -e "\e[32m$PROMETHEUS_ALERT_NAME target and alert rules file added, and Prometheus reloaded.\e[0m"
else
    echo "Prometheus configuration file not found at ${PROMETHEUS_CONFIG_PATH}."
    echo "Please ensure Prometheus is installed and the configuration file path is correct."
fi

# Step 10: Clean up
rm alertmanager-0.25.0.linux-amd64.tar.gz
rm -rf alertmanager-0.25.0.linux-amd64
echo -e "\e[32m$PROMETHEUS_ALERT_NAME cleaned up\e[0m"
