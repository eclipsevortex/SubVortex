#!/bin/bash

# Usage: ./check_ssl_nginx.sh your.domain.com

set -e

DOMAIN=$1
IP="127.0.0.1"
NGINX_DEFAULT_PORT=443

if [ -z "$DOMAIN" ]; then
  echo "❌ Usage: $0 your.domain.com"
  exit 1
fi

echo "🔍 Checking NGINX service status..."
sudo systemctl is-active --quiet nginx && echo "✅ NGINX is running." || { echo "❌ NGINX is not running."; exit 1; }

echo "🧪 Testing NGINX configuration syntax..."
if sudo nginx -t; then
  echo "✅ NGINX configuration syntax is OK."
else
  echo "❌ NGINX configuration error!"
  exit 1
fi

echo "🌐 Curl test to local HTTPS endpoint..."
curl -s -o /dev/null -w "%{http_code}\n" --resolve "$DOMAIN:$NGINX_DEFAULT_PORT:$IP" "https://$DOMAIN" | grep -q "200" \
  && echo "✅ HTTPS endpoint is serving successfully." \
  || echo "⚠️ HTTPS endpoint did not return HTTP 200."

echo "🔐 Checking SSL certificate details..."
echo | openssl s_client -connect "$DOMAIN:$NGINX_DEFAULT_PORT" -servername "$DOMAIN" 2>/dev/null | openssl x509 -noout -text | grep -E "Subject:|Issuer:|Not Before:|Not After :"

echo "🕵️ Checking for padlock (manual step)..."
echo "👉 Please visit https://$DOMAIN in your browser and check for the 🔒 padlock."

echo "📊 Want a deeper check? Try SSL Labs at:"
echo "🔗 https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"

echo "📂 Tailing last 10 lines of NGINX error log:"
sudo tail -n 10 /var/log/nginx/error.log

echo "✅ All checks completed."
