#!/usr/bin/env bash
set -euo pipefail

COMPONENT="$1"
SERVICE="$2"
TAG="$3"

VERSION="${TAG#v}"
REPO_NAME="subvortex-$COMPONENT-${SERVICE//_/-}"
IMAGE="subvortex/$REPO_NAME"

DOCKER_USERNAME="${DOCKER_USERNAME:-}"
DOCKER_PASSWORD="${DOCKER_PASSWORD:-}"

if [[ -z "$DOCKER_USERNAME" || -z "$DOCKER_PASSWORD" ]]; then
  echo "❌ Missing Docker credentials (DOCKER_USERNAME / DOCKER_PASSWORD)"
  exit 1
fi

echo "🔐 Requesting Docker Hub JWT token..."
TOKEN=$(curl -s -X POST https://hub.docker.com/v2/users/login/ \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$DOCKER_USERNAME\", \"password\": \"$DOCKER_PASSWORD\"}" | jq -r .token)

if [[ "$TOKEN" == "null" || -z "$TOKEN" ]]; then
  echo "❌ Failed to authenticate with Docker Hub"
  exit 1
fi

echo "🔍 Deleting $IMAGE:$VERSION from Docker Hub..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
  -H "Authorization: JWT $TOKEN" \
  "https://hub.docker.com/v2/repositories/$DOCKER_USERNAME/$REPO_NAME/tags/$VERSION/")

case "$RESPONSE" in
  204)
    echo "✅ Deleted $IMAGE:$VERSION"
    ;;
  404)
    echo "⚠️ Tag not found: $IMAGE:$VERSION"
    ;;
  *)
    echo "❌ Failed to delete tag: HTTP $RESPONSE"
    exit 1
    ;;
esac
