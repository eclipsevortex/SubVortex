#!/bin/bash
set -e

CERT_DIR="/etc/letsencrypt/live/fullchain_subvortex.info.crt"
SOURCE_DIR="/root/subvortex/subvortex/scripts/wss/prod"
NGINX_DEFAULT="/etc/nginx/sites-available/default"
NEEDS_RELOAD=false

echo "🔄 Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo "🌐 Checking for NGINX..."
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing NGINX..."
    sudo apt install nginx -y
else
    echo "✅ NGINX is already installed."
fi

echo "🛡️  Configuring firewall for NGINX..."
for rule in 'Nginx HTTP' 'Nginx HTTPS'; do
    if ! sudo ufw status | grep -qw "$rule"; then
        echo "➕ Allowing $rule"
        sudo ufw allow "$rule"
    else
        echo "✅ Firewall rule '$rule' already allowed"
    fi
done

echo "📦 Checking for snapd..."
if ! command -v snap &> /dev/null; then
    echo "📦 Installing snapd..."
    sudo apt install snapd -y
else
    echo "✅ snapd is already installed."
fi

echo "🧩 Checking for Snap core..."
if ! snap list core &>/dev/null; then
    echo "📦 Installing snap core..."
    sudo snap install core
else
    echo "🔄 Refreshing snap core..."
    sudo snap refresh core
fi

echo "🔐 Checking for Certbot..."
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing Certbot..."
    sudo snap install --classic certbot
    sudo ln -sf /snap/bin/certbot /usr/bin/certbot
else
    echo "✅ Certbot is already installed."
fi

echo "📁 Preparing certificate directory: $CERT_DIR"
sudo mkdir -p "$CERT_DIR"

echo "📄 Checking if TLS assets need to be copied..."
for file in fullchain.pem privkey.pem; do
    if [ "$SOURCE_DIR/$file" -nt "$CERT_DIR/$file" ]; then
        echo "⚙️  Copying updated $file"
        sudo cp "$SOURCE_DIR/$file" "$CERT_DIR/"
        NEEDS_RELOAD=true
    else
        echo "✅ $file is up to date"
    fi
done

for file in options-ssl-nginx.conf ssl-dhparams.pem; do
    if [ "$SOURCE_DIR/$file" -nt "/etc/letsencrypt/$file" ]; then
        echo "⚙️  Updating $file"
        sudo cp "$SOURCE_DIR/$file" /etc/letsencrypt/
        NEEDS_RELOAD=true
    else
        echo "✅ $file is up to date"
    fi
done

if [ "$SOURCE_DIR/README" -nt "$CERT_DIR/README" ]; then
    echo "⚙️  Updating README"
    sudo cp "$SOURCE_DIR/README" "$CERT_DIR/"
fi

if [ -f "$SOURCE_DIR/default" ]; then
    if ! cmp -s "$SOURCE_DIR/default" "$NGINX_DEFAULT"; then
        echo "📄 NGINX config has changed. Backing up and updating..."
        sudo cp "$NGINX_DEFAULT" "${NGINX_DEFAULT}_old_$(date +%Y%m%d%H%M%S)" || true
        sudo cp "$SOURCE_DIR/default" "$NGINX_DEFAULT"
        NEEDS_RELOAD=true
    else
        echo "✅ NGINX config is up to date."
    fi
fi

if [ "$NEEDS_RELOAD" = true ]; then
    echo "🚀 Reloading NGINX to apply changes..."
    sudo nginx -t && sudo systemctl reload nginx
else
    echo "✅ No changes detected. NGINX reload skipped."
fi

echo "🎉 Setup complete! NGINX is running with your SSL configuration."
