#!/bin/bash
set -e

CERT_DIR="/etc/letsencrypt/live/fullchain_subvortex.info.crt"
NGINX_DEFAULT="/etc/nginx/sites-available/default"
UFW_RULES=("Nginx HTTP" "Nginx HTTPS")

echo "⚠️ Starting full teardown of NGINX + SSL configuration..."

# Stop and remove NGINX
if command -v nginx &>/dev/null; then
    echo "🛑 Stopping NGINX..."
    sudo systemctl stop nginx || true

    echo "🧹 Removing NGINX packages..."
    sudo apt purge -y nginx nginx-common
    sudo apt autoremove -y
else
    echo "✅ NGINX is already removed."
fi

# Restore backup config if available
LATEST_BACKUP=$(ls -t /etc/nginx/sites-available/default_old_* 2>/dev/null | head -n 1)
if [ -f "$LATEST_BACKUP" ]; then
    echo "🔁 Restoring original NGINX default config from backup..."
    sudo cp "$LATEST_BACKUP" "$NGINX_DEFAULT"
else
    echo "ℹ️ No NGINX default config backup found."
fi

# Remove UFW rules
echo "🧯 Removing UFW rules for NGINX..."
for rule in "${UFW_RULES[@]}"; do
    if sudo ufw status | grep -qw "$rule"; then
        echo "🚫 Removing UFW rule: $rule"
        sudo ufw delete allow "$rule"
    else
        echo "✅ UFW rule '$rule' already removed or not present."
    fi
done

# Remove TLS certificate directory
if [ -d "$CERT_DIR" ]; then
    echo "🗑️ Removing certificate directory: $CERT_DIR"
    sudo rm -rf "$CERT_DIR"
else
    echo "✅ Certificate directory already removed."
fi

# Remove shared Certbot assets
for file in options-ssl-nginx.conf ssl-dhparams.pem; do
    TARGET="/etc/letsencrypt/$file"
    if [ -f "$TARGET" ]; then
        echo "🧼 Removing $TARGET"
        sudo rm -f "$TARGET"
    else
        echo "✅ $file already removed."
    fi
done

# Remove Certbot
if command -v certbot &>/dev/null; then
    echo "🧹 Removing Certbot..."
    sudo snap remove certbot || true
    sudo rm -f /usr/bin/certbot
else
    echo "✅ Certbot already removed."
fi

# Remove Snap Core if installed
if snap list core &>/dev/null; then
    echo "🧹 Removing Snap Core..."
    sudo snap remove core || true
else
    echo "✅ Snap Core already removed."
fi

# Final cleanup
echo "🔄 Reloading UFW and finishing up..."
sudo ufw reload || true

echo "✅ Teardown complete: NGINX and SSL configuration have been fully removed."
