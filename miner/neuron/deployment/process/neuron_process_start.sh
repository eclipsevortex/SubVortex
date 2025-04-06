#!/bin/bash

set -e

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Activate virtual environment
source venv/bin/activate

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Run the process
pm2 start src/main.py \
    --name miner \
    --interpreter python3 -- \
    --wallet.name "${TENSORDAEMON_WALLET}" \
    --wallet.hotkey "${TENSORDAEMON_HOTKEY}" \
    --netuid "${TENSORDAEMON_NETUID:-7}" \
    $( [ -n "${TENSORDAEMON_IP:-}" ] && echo "--axon.ip ${TENSORDAEMON_IP}" ) \
    --axon.port "${TENSORDAEMON_PORT}" \
    --axon.external_port "${TENSORDAEMON_EXTERNAL_PORT}" \
    --subtensor.network "${TENSORDAEMON_SUBTENSOR}" \
    --proxy.socket "${TENSORDAEMON_PROXY_SOCKET}"

echo "✅ Miner started successfully"
