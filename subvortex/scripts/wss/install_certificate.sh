#!/bin/bash

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
sudo ufw allow 'Nginx HTTP'
sudo ufw allow 'Nginx HTTPS'

echo "📦 Checking for snapd..."
if ! command -v snap &> /dev/null; then
    echo "📦 Installing snapd..."
    sudo apt install snapd -y
fi

echo "🔄 Ensuring snap core is up to date..."
sudo snap install core || true
sudo snap refresh core

echo "🔐 Checking for Certbot..."
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing Certbot..."
    sudo snap install --classic certbot
    sudo ln -s /snap/bin/certbot /usr/bin/certbot
else
    echo "✅ Certbot is already installed."
fi

CERT_DIR="/etc/letsencrypt/live/fullchain_subvortex.info.crt"
echo "📁 Preparing certificate directory: $CERT_DIR"
sudo mkdir -p "$CERT_DIR"

echo "📄 Copying TLS assets..."
sudo cp /root/subvortex/subvortex/scripts/wss/prod/*.pem "$CERT_DIR"/
sudo cp /root/subvortex/subvortex/scripts/wss/prod/README "$CERT_DIR"/
sudo cp /root/subvortex/subvortex/scripts/wss/prod/options-ssl-nginx.conf /etc/letsencrypt/
sudo cp /root/subvortex/subvortex/scripts/wss/prod/ssl-dhparams.pem /etc/letsencrypt/

NGINX_DEFAULT="/etc/nginx/sites-available/default"
if [ -f "$NGINX_DEFAULT" ]; then
    echo "📦 Backing up default NGINX config..."
    sudo mv "$NGINX_DEFAULT" "${NGINX_DEFAULT}_old"
fi

echo "📄 Deploying custom NGINX config..."
sudo cp /root/subvortex/subvortex/scripts/wss/prod/default "$NGINX_DEFAULT"

echo "🚀 Restarting NGINX..."
sudo systemctl restart nginx

echo "✅ Setup complete! NGINX is running with your SSL configuration."
