#!/bin/bash
set -euo pipefail

echo "🔧 Stopping Redis service (if running)..."
sudo systemctl stop redis-server.service || true
sudo systemctl disable redis-server.service || true
sudo systemctl mask redis-server.service || true

# --- Remove redis-server based on package manager ---
if command -v apt-get &> /dev/null; then
  if dpkg -l | grep -q redis-server; then
    echo "📦 Removing redis-server via APT..."
    sudo apt-get remove --purge -y redis-server redis-tools || true
    sudo apt-get autoremove -y
    sudo apt-get autoclean
  fi

  echo "🧼 Cleaning Redis APT sources..."
  sudo rm -f /etc/apt/sources.list.d/redis.list
  sudo rm -f /usr/share/keyrings/redis-archive-keyring.gpg

elif command -v dnf &> /dev/null; then
  if rpm -q redis &> /dev/null || rpm -q redis-server &> /dev/null; then
    echo "📦 Removing redis via DNF..."
    sudo dnf remove -y redis redis-utils || true
  fi

  echo "🧼 Cleaning Redis DNF/YUM repos..."
  sudo rm -f /etc/yum.repos.d/redis.repo

elif command -v pacman &> /dev/null; then
  if pacman -Qi redis &> /dev/null; then
    echo "📦 Removing redis via Pacman..."
    sudo pacman -Rns --noconfirm redis || true
  fi
fi

# --- Clean files and residuals ---
echo "🧹 Removing Redis configuration, logs, and data..."
sudo rm -rf /etc/redis
sudo rm -rf /var/log/redis
sudo rm -rf /var/lib/redis

# Remove potential leftover systemd unit
sudo rm -f /etc/systemd/system/redis.service
sudo rm -f /etc/systemd/system/redis-server.service
sudo systemctl daemon-reload

# --- Clean binaries from common paths ---
echo "🗑️ Removing Redis binaries from all known locations..."

BIN_PATHS=(
  "/usr/local/bin/redis-server"
  "/usr/local/bin/redis-cli"
  "/usr/bin/redis-server"
  "/usr/bin/redis-cli"
  "/usr/sbin/redis-server"
  "/usr/sbin/redis-cli"
)

for bin in "${BIN_PATHS[@]}"; do
  if [[ -f "$bin" ]]; then
    echo "❌ Removing $bin"
    sudo rm -f "$bin"
  fi
done

# --- Clean manually installed configs and data dirs ---
sudo rm -rf /usr/local/etc/redis
sudo rm -rf /usr/local/var/redis

echo "✅ Redis Server cleanup complete."