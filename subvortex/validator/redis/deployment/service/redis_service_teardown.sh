#!/bin/bash
set -euo pipefail

NEURON_NAME="subvortex-validator"
SERVICE_NAME="$NEURON_NAME-redis"
CHECKSUM_DIR="/var/tmp/dumps/redis/${SERVICE_NAME}-checksums"

echo "📦 Starting teardown for $SERVICE_NAME..."

# Stop and disable the systemd service if it exists
if systemctl list-units --type=service --all | grep -q "${SERVICE_NAME}.service"; then
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "🛑 Stopping systemd service: $SERVICE_NAME..."
        sudo systemctl stop "${SERVICE_NAME}.service"
    fi

    echo "🚫 Disabling systemd service: $SERVICE_NAME..."
    sudo systemctl disable "${SERVICE_NAME}.service"

    echo "🧹 Removing systemd service file..."
    sudo rm -f "/etc/systemd/system/${SERVICE_NAME}.service"

    echo "🔄 Reloading systemd daemon..."
    sudo systemctl daemon-reexec
    sudo systemctl daemon-reload
else
    echo "ℹ️ Systemd service ${SERVICE_NAME}.service not found. Skipping stop/disable."
fi

# Remove log directory
LOG_DIR="/var/log/$NEURON_NAME"
if [[ -d "$LOG_DIR" ]]; then
    echo "🧹 Removing log directory: $LOG_DIR"
    sudo rm -rf "$LOG_DIR"
else
    echo "ℹ️ Log directory $LOG_DIR does not exist. Skipping."
fi

# Remove checksum directory
if [[ -d "$CHECKSUM_DIR" ]]; then
    echo "🧽 Removing checksum directory: $CHECKSUM_DIR"
    sudo rm -rf "$CHECKSUM_DIR"
else
    echo "ℹ️ Checksum directory $CHECKSUM_DIR does not exist. Skipping."
fi

# Remove redis-server package if installed
echo "🔍 Checking if redis-server is installed..."
if dpkg -s redis-server >/dev/null 2>&1; then
    echo "🧼 Removing redis-server package..."
    sudo apt purge -y redis-server
    sudo apt autoremove -y
else
    echo "ℹ️ redis-server not installed. Nothing to remove."
fi

echo "✅ Validator Redis teardown completed successfully."
