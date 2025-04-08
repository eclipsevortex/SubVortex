#!/bin/bash

set -e

SERVICE_NAME=subvortex-miner

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Activate virtual environment
source venv/bin/activate

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Install the service configuration
envsubst < "./deployment/templates/${SERVICE_NAME}.service" | tee "/etc/systemd/system/${SERVICE_NAME}.service" > /dev/null

# Prepare the log
sudo mkdir -p /var/log/$SERVICE_NAME
sudo chown root:root /var/log/$SERVICE_NAME

## Start the service
systemctl daemon-reload
systemctl restart $SERVICE_NAME.service
systemctl enable $SERVICE_NAME.service

echo "✅ Miner started successfully"
