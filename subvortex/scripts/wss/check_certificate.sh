#!/bin/bash

set -e

DOMAIN=${1:-secure.subvortex.info}
IP="127.0.0.1"
NGINX_DEFAULT_PORT=443

if [ -z "$DOMAIN" ]; then
  echo "❌ Usage: $0 your.domain.com"
  exit 1
fi

echo "🔍 Checking NGINX service status..."
if sudo systemctl is-active --quiet nginx; then
  echo "✅ NGINX is running."
else
  echo "❌ NGINX is not running."
  exit 1
fi

echo "🧪 Testing NGINX configuration syntax..."
if sudo nginx -t; then
  echo "✅ NGINX configuration syntax is OK."
else
  echo "❌ NGINX configuration error!"
  exit 1
fi

echo "🌐 Curl test to LOCAL HTTPS endpoint using local IP and Host header..."
curl -s -o /dev/null -w "HTTP %{http_code}\n" --resolve "$DOMAIN:$NGINX_DEFAULT_PORT:$IP" "https://$DOMAIN/" || {
  echo "❌ Failed to connect to local HTTPS endpoint."
  exit 1
}

echo "🔐 Fetching SSL certificate served by local NGINX instance..."

CERT_INFO=$(echo | openssl s_client -connect "$IP:$NGINX_DEFAULT_PORT" -servername "$DOMAIN" 2>/dev/null | openssl x509 -noout -subject -issuer -enddate)

SUBJECT=$(echo "$CERT_INFO" | grep "subject=" | sed 's/subject=//')
ISSUER=$(echo "$CERT_INFO" | grep "issuer=" | sed 's/issuer=//')
END_DATE=$(echo "$CERT_INFO" | grep "notAfter=" | cut -d= -f2)

echo "📛 Subject (Who this cert is for): $SUBJECT"
echo "🏢 Issuer (Who issued the cert): $ISSUER"
echo "📅 Expiration: $END_DATE"

# Domain match check
if echo "$SUBJECT" | grep -q "$DOMAIN"; then
  echo "✅ Certificate matches $DOMAIN"
else
  echo "⚠️ WARNING: Certificate subject does NOT match $DOMAIN"
fi

# Let's Encrypt check
if echo "$ISSUER" | grep -qi "let's encrypt"; then
  echo "✅ Certificate was issued by Let's Encrypt"
else
  echo "⚠️ WARNING: Certificate was NOT issued by Let's Encrypt"
fi

echo "📂 Tailing last 10 lines of NGINX error log:"
sudo tail -n 10 /var/log/nginx/error.log

echo "✅ All checks complete on LOCAL VPS."
