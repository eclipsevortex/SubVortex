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

# Define deployment paths
DEPLOY_SOURCE="$SCRIPT_DIR/../../../../../"
DEPLOY_SOURCE=$(resolve_path "$DEPLOY_SOURCE")
DEPLOY_LINK="$HOME/subvortex"

# Create parent directory if needed
mkdir -p "$(dirname "$DEPLOY_LINK")"

# Atomically update symlink
TEMP_LINK="${DEPLOY_LINK}.tmp"

# Create/update the temp symlink
ln -sfn "$DEPLOY_SOURCE" "$TEMP_LINK"

# On macOS and Linux: remove old symlink and rename temp
if [ -L "$DEPLOY_LINK" ] || [ -e "$DEPLOY_LINK" ]; then
  rm -rf "$DEPLOY_LINK"
fi
mv "$TEMP_LINK" "$DEPLOY_LINK"

echo "🔗 Symlink set: $DEPLOY_LINK → $DEPLOY_SOURCE"

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
