#!/usr/bin/env bash

set -euo pipefail

echo "🚀 Starting PM2 installation..."

# Detect platform
OS="$(uname)"
ARCH="$(uname -m)"

# Install Node.js
install_node_linux() {
    echo "🔧 Installing Node.js on Linux..."

    if command -v apt-get &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    elif command -v yum &> /dev/null; then
        curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
        sudo yum install -y nodejs
    elif command -v apk &> /dev/null; then
        apk add --no-cache nodejs npm
    else
        echo "❌ Unsupported Linux distribution."
        exit 1
    fi
}

install_node_macos() {
    echo "🍏 Installing Node.js on macOS..."

    if ! command -v brew &> /dev/null; then
        echo "📦 Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi

    brew install node
}

# Install PM2
install_pm2() {
    echo "📦 Installing PM2..."
    sudo npm install -g pm2
    pm2 --version
    echo "✅ PM2 installed successfully!"
}

if [[ "$OS" == "Linux" ]]; then
    install_node_linux
elif [[ "$OS" == "Darwin" ]]; then
    install_node_macos
else
    echo "❌ Unsupported operating system: $OS"
    exit 1
fi

install_pm2

echo "🎉 Installation complete! Try: pm2 list"
