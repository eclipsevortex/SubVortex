#!/bin/bash

set -euo pipefail

echo "🧨 Starting PM2 teardown..."

OS="$(uname)"

# Step 1: Stop all PM2 processes (if PM2 is installed)
if command -v pm2 >/dev/null; then
    echo "🛑 Stopping all PM2 processes..."
    pm2 stop all || true
    pm2 delete all || true

    echo "❌ Disabling PM2 boot startup..."
    if [[ "$OS" == "Linux" ]]; then
        pm2 unstartup systemd || true
    elif [[ "$OS" == "Darwin" ]]; then
        pm2 unstartup launchd || true
    fi

    echo "🧽 Uninstalling PM2..."
    sudo npm uninstall -g pm2
else
    echo "ℹ️ PM2 is not installed — skipping."
fi

# Step 2: Optional — uninstall Node.js
UNINSTALL_NODE=false  # Change to true to uninstall Node.js too

if $UNINSTALL_NODE; then
    echo "💥 Uninstalling Node.js..."

    if [[ "$OS" == "Darwin" ]]; then
        if command -v brew >/dev/null; then
            brew uninstall node || true
        fi
    elif [[ "$OS" == "Linux" ]]; then
        sudo apt-get remove -y nodejs npm || true
    fi
fi

echo "✅ PM2 teardown completed."
