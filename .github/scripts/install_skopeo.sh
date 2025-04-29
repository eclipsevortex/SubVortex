#!/usr/bin/env bash
set -euo pipefail

echo "📦 Checking if skopeo is installed..."

if command -v skopeo >/dev/null 2>&1; then
  echo "✅ skopeo already installed."
  exit 0
fi

echo "🔍 skopeo not found — installing..."

# Detect OS
OS="$(uname -s)"

if [[ "$OS" == "Darwin" ]]; then
  # macOS
  if ! command -v brew >/dev/null 2>&1; then
    echo "❌ Homebrew is not installed. Install it from https://brew.sh/"
    exit 1
  fi
  brew install skopeo
elif [[ "$OS" == "Linux" ]]; then
  # Linux
  if command -v apt-get >/dev/null 2>&1; then
    # Debian/Ubuntu
    sudo apt-get update
    sudo apt-get install -y skopeo
  elif command -v dnf >/dev/null 2>&1; then
    # Fedora
    sudo dnf install -y skopeo
  elif command -v yum >/dev/null 2>&1; then
    # RHEL/CentOS 7
    sudo yum install -y skopeo
  else
    echo "❌ Unsupported Linux distribution. Please install skopeo manually."
    exit 1
  fi
else
  echo "❌ Unsupported OS: $OS"
  exit 1
fi

echo "✅ skopeo installed successfully."
