#!/bin/bash

set -e

SERVICE_NAME="subvortex-miner-neuron"

# Check if PM2 process is running and stop it
if pm2 list | grep -q "$SERVICE_NAME"; then
  echo "🛑 Stopping $SERVICE_NAME"
  pm2 stop "$SERVICE_NAME"
else
  echo "ℹ️ $SERVICE_NAME is not running"
fi
